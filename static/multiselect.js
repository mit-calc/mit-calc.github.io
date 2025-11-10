const COUNTRIES = [
    "Argentina",
    "Australia",
    "Austria",
    "Belgium",
    "Brazil",
    "Canada",
    "China",
    "Denmark",
    "EU",
    "Finland",
    "France",
    "Germany",
    "India",
    "Israel",
    "Italy",
    "Japan",
    "Mexico",
    "Netherlands",
    "New Zealand",
    "Norway",
    "Poland",
    "Saudi Arabia",
    "Singapore",
    "South Africa",
    "South Korea",
    "Spain",
    "Sweden",
    "Switzerland",
    "UAE",
    "UK",
    "USA"
];

const LLM_MODELS = [
    "BERT",
    "Claude",
    "Flan-T5",
    "Google PaLM",
    "Meta LLAMA",
    "OpenAI GPT2",
    "OpenAI GPT3",
    "OpenAI GPT3.5",
    "OpenAI GPT4",
    "RoBERTa"
];

const FUNDING_TYPES = [
    "Corporate",
    "Foundation",
    "Government"
];

// Configuration for each multi-select field
const MULTI_SELECT_CONFIG = {
    "Funding Resource": {
        options: COUNTRIES,
        placeholder: "Select a country..."
    },
    "Funding Type": {
        options: FUNDING_TYPES,
        placeholder: "Select funding type..."
    },
    "LLM(s) FineTuning": {
        options: LLM_MODELS,
        placeholder: "Select LLM..."
    },
    "LLM(s) Evaluation": {
        options: LLM_MODELS,
        placeholder: "Select LLM..."
    }
};