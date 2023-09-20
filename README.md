# RAG-Constitucion-Chile

Platform to compare Chile's current constitution with its new proposed constitution. This is a proof-of-concept using RAG where the sources are the articles from each constitution. You can check out a demo here: https://rag-constitucion-chile.streamlit.app/ . Coming soon to https://discolab.cl/ 

## Getting Started

Before you begin to run this project, there are a few prerequisites you will need to have in place:

✅ **OpenAI API Key:** In order to interact with OpenAI's API, you will need to have an API key. You can obtain this by creating an account on OpenAI's website and following their [instructions to generate an API key](https://help.openai.com/en/articles/4936850-where-do-i-find-my-secret-api-key).

✅ **Modal Account:** The application is containerized for deployment using the Modal platform. Visit the [Modal](https://modal.com/signup) website to sign up for an account if you don't have one already.

✅ **Streamlit Account (Optional):** While you can run Streamlit apps locally without an account, having a Streamlit account allows you to deploy and share your apps, which can be useful for demonstrating your project to others. If you wish to use this feature, [sign up for a Streamlit account](https://share.streamlit.io/signup).

## Installation

```
conda create --name rag-constitucion-chile -c conda-forge python=3.10
conda activate rag-constitucion-chile
pip install -r requirements.txt
```

## [CLIENT] Streamlit app

```
streamlit run st_app.py
```
