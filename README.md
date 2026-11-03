# DNA Vault

A software simulation of DNA data storage. Upload a file, encode it as A/C/G/T strands,
inject synthesis and sequencing errors, and recover the original file using CRC checks,
read consensus and Reed-Solomon error correction. Integrity is verified with SHA-256.

This is a simulation. No physical DNA is synthesised.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Run experiments
    python experiments.py

## Files
- dnavault.py: encoder, channel simulator, decoder
- app.py: Streamlit web interface
- experiments.py: reproducible experiments (results in results.md)

## Live Demo
Try it in your browser, no installation needed:

[Open DNA Vault](https://dna-vault-fdf96ip4f3ovggapm7wfdq.streamlit.app/)

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://dna-vault-fdf96ip4f3ovggapm7wfdq.streamlit.app/)
