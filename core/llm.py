"""Configurable hosted LLM for all analysis and question-answering chains."""
import utils.env_setup  # Enforces safe drive paths and env before imports
import logging
import os
import time
from threading import Lock

import httpx
from langchain_mistralai import ChatMistralAI
from huggingface_hub import InferenceClient
from langchain_core.messages import AIMessage
from langchain_core.messages.utils import convert_to_openai_messages
from langchain_core.runnables import RunnableLambda
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)
_backoff = wait_exponential_jitter(initial=15, max=60)
_request_lock = Lock()
_last_request = 0.0
_groq_lock = Lock()
_last_groq_request = 0.0


def _is_rate_limit(error):
    return isinstance(error, httpx.HTTPStatusError) and error.response.status_code == 429


def _retry_delay(state):
    error = state.outcome.exception()
    header = error.response.headers.get('Retry-After')
    try:
        return max(_backoff(state), float(header)) if header else _backoff(state)
    except ValueError:
        return _backoff(state)


class RateLimitMistral(ChatMistralAI):
    @retry(
        retry=retry_if_exception(_is_rate_limit),
        wait=_retry_delay,
        stop=stop_after_attempt(4),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def completion_with_retry(self, run_manager=None, **kwargs):
        global _last_request
        # Shared across clients and Streamlit sessions in this server process.
        with _request_lock:
            delay = 2.0 - (time.monotonic() - _last_request)
            if delay > 0:
                time.sleep(delay)
            _last_request = time.monotonic()
            return super().completion_with_retry(run_manager=run_manager, **kwargs)


def _get_mistral_llm(temperature=0.3):
    api_key = os.getenv('MISTRAL_API_KEY', '').strip()
    if not api_key:
        raise ValueError('MISTRAL_API_KEY is not set in environment or .env')
    model = os.getenv('MISTRAL_MODEL', 'mistral-small-2603').strip()
    return RateLimitMistral(
        model=model,
        mistral_api_key=api_key,
        temperature=temperature,
        max_tokens=1024,
    )


def _get_groq_llm(temperature=0.3):
    api_key = os.getenv('GROQ_API_KEY', '').strip()
    if not api_key:
        raise ValueError('Groq is not configured. Add GROQ_API_KEY to your Streamlit secrets or local .env.')
    model = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b').strip()

    @retry(retry=retry_if_exception(_is_rate_limit), wait=_retry_delay,
           stop=stop_after_attempt(4), before_sleep=before_sleep_log(logger, logging.WARNING), reraise=True)
    def complete(prompt):
        global _last_groq_request
        messages = prompt.to_messages() if hasattr(prompt, 'to_messages') else prompt
        payload = {
            'model': model, 'messages': convert_to_openai_messages(messages),
            'temperature': temperature, 'max_completion_tokens': 2048,
        }
        if model.startswith('openai/gpt-oss'):
            payload['reasoning_effort'] = 'low'
        with _groq_lock:
            delay = 2.0 - (time.monotonic() - _last_groq_request)
            if delay > 0:
                time.sleep(delay)
            _last_groq_request = time.monotonic()
            response = httpx.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={'Authorization': f'Bearer {api_key}'}, json=payload, timeout=120,
            )
            response.raise_for_status()
        choice = response.json()['choices'][0]
        if choice.get('finish_reason') == 'length':
            raise RuntimeError('Groq reached the response length limit. Try a shorter transcript.')
        content = choice['message'].get('content')
        if not content:
            raise RuntimeError('Groq returned no answer. Please try again.')
        return AIMessage(content=content)

    return RunnableLambda(complete)


def create_llm(temperature=0.3, provider=None):
    provider = (provider or os.getenv('LLM_PROVIDER', 'mistral')).strip().lower()

    if provider == 'groq':
        return _get_groq_llm(temperature)

    if provider == 'mistral':
        return _get_mistral_llm(temperature)

    if provider == 'huggingface':
        token = os.getenv('HF_TOKEN', '').strip()
        if not token:
            if os.getenv('MISTRAL_API_KEY'):
                logger.warning('HF_TOKEN is missing, falling back to Mistral.')
                return _get_mistral_llm(temperature)
            raise ValueError('Set HF_TOKEN in .env or set MISTRAL_API_KEY to use Mistral.')

        client = InferenceClient(
            base_url='https://router.huggingface.co/v1',
            api_key=token,
            timeout=120,
        )
        model = os.getenv('HF_MODEL', 'openai/gpt-oss-120b:cheapest')

        @retry(
            retry=retry_if_exception(_is_rate_limit),
            wait=_retry_delay,
            stop=stop_after_attempt(4),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        def complete(prompt):
            messages = prompt.to_messages() if hasattr(prompt, 'to_messages') else prompt
            try:
                response = client.chat_completion(
                    model=model,
                    messages=convert_to_openai_messages(messages),
                    temperature=temperature,
                    max_tokens=2048,
                )
                content = response.choices[0].message.content
                if not content:
                    raise RuntimeError('Hugging Face returned no answer.')
                return AIMessage(content=content)
            except Exception as e:
                # If Hugging Face failed (e.g. 402 Payment Required) and Mistral key is available, fallback to Mistral
                if os.getenv('MISTRAL_API_KEY'):
                    logger.warning(f'Hugging Face call failed ({e}), falling back to Mistral.')
                    mistral_llm = _get_mistral_llm(temperature)
                    return mistral_llm.invoke(prompt)
                raise

        return RunnableLambda(complete)

    raise ValueError(f'Unknown LLM_PROVIDER: {provider}. Must be mistral, groq, or huggingface.')
