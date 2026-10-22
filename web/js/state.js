/**
 * Crewlyze - Global State & Constants Store (ES6 Module)
 */

export const DEFAULT_THUMBNAIL_SVG = '/assets/placeholder_thumbnail.png';

export const MODEL_OPTIONS = {
  nvidia: [
    'nvidia_nim/meta/llama-3.1-70b-instruct',
    'nvidia_nim/meta/llama-3.1-405b-instruct',
    'nvidia_nim/meta/llama-3.2-1b-instruct',
    'nvidia_nim/meta/llama-3.2-3b-instruct',
    'nvidia_nim/nvidia/llama-3.1-nemotron-70b-instruct',
    'nvidia_nim/nvidia/llama-3.1-nemotron-51b-instruct',
    'nvidia_nim/nvidia/mistral-nemo-minitron-8b-8k-instruct',
    'nvidia_nim/nvidia/nemotron-4-340b-instruct',
    'nvidia_nim/nvidia/nemotron-mini-4b-instruct',
    'nvidia_nim/mistralai/mistral-large-2407',
    'nvidia_nim/mistralai/mistral-7b-instruct-v0.3',
    'nvidia_nim/mistralai/mixtral-8x7b-instruct-v01',
    'nvidia_nim/mistralai/mixtral-8x22b-instruct-v01',
    'nvidia_nim/google/gemma-2-9b-it',
    'nvidia_nim/google/gemma-2-27b-it',
    'nvidia_nim/microsoft/phi-3-mini-128k-instruct',
    'nvidia_nim/microsoft/phi-3-medium-128k-instruct',
    'nvidia_nim/microsoft/phi-3-small-128k-instruct',
    'nvidia_nim/qwen/qwen2-7b-instruct',
    'nvidia_nim/databricks/dbrx-instruct',
    'nvidia_nim/01-ai/yi-large',
    'nvidia_nim/aisingapore/sea-lion-7b-instruct',
    'nvidia_nim/ibm/granite-34b-code-instruct',
    'nvidia_nim/upstage/solar-10.7b-instruct',
    'nvidia_nim/snowflake/arctic-instruct',
    'nvidia_nim/writer/palmyra-med-70b-32k',
    'nvidia_nim/writer/palmyra-fin-70b-32k',
  ],
  minimax: ['minimaxai/minimax-m3'],
  groq: ['groq/llama-3.3-70b-versatile', 'groq/llama-3.1-8b-instant', 'groq/mixtral-8x7b-32768', 'groq/gemma2-9b-it'],
  openai: ['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
  gemini: ['gemini/gemini-1.5-flash', 'gemini/gemini-1.5-pro', 'gemini/gemini-2.0-flash'],
  mistral: ['mistral/mistral-small-latest', 'mistral/mistral-large-latest', 'mistral/open-mixtral-8x7b'],
  huggingface: ['huggingface/HuggingFaceH4/zephyr-7b-beta', 'huggingface/meta-llama/Llama-2-7b-chat-hf'],
  ollama: ['ollama/llama3', 'ollama/mistral', 'ollama/gemma2'],
  custom: ['gpt-3.5-turbo', 'gpt-4'],
  cohere: ['cohere/command-r-plus', 'cohere/command-r', 'cohere/command-light'],
  together: ['together_ai/meta-llama/Llama-3-70b-chat-hf', 'together_ai/meta-llama/Llama-3-8b-chat-hf', 'together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1'],
  openrouter: ['openrouter/google/gemma-2-9b-it', 'openrouter/meta-llama/llama-3-8b-instruct', 'openrouter/anthropic/claude-3.5-sonnet'],
  deepseek: ['deepseek/deepseek-chat', 'deepseek/deepseek-coder'],
  perplexity: ['perplexity/llama-3-sonar-large-32k-chat', 'perplexity/llama-3-sonar-small-32k-chat'],
};

export const state = {
  projects: [],
  activeProject: null,
  uploadedFile: null,
  uploadedSession: null,
  results: null,
  columns: [],
  colTypes: {},
  chatHistory: [],
  previewMinimized: false,
  sseSource: null,
  resultsCache: {},
  smtpAccounts: [],
};

export const $ = id => document.getElementById(id);
export const $$ = sel => document.querySelectorAll(sel);

// Attach globally for inline HTML attributes / legacy interop
if (typeof window !== 'undefined') {
  window.crewlyzeState = state;
}
