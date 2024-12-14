# bluesky-bob

This repository contains code that responds to messages on [bluesky](https://bsky.app/) using large language models via [Github Models Marketplace](https://github.com/marketplace) and the [atproto API](https://github.com/MarshalX/atproto). 
It runs in the github CI using hourly [scheduled cron jobs](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule).
It will only respond to messages from accounts that it follows.
You can see it in action [here](https://bsky.app/profile/haesleinhuepf-bot.bsky.social/post/3lcg5xe2b5i2h).
The bot currently also posts updates from selected Zenodo communities, which is implemented and human-curated [here](https://github.com/haesleinhuepf/zenodo-bluesky-bob).

This is an academic research project and not intended to be used in production.

## Installation

To run this under your own account, you need clone the repository, activate Github actions and configure three secrets in your repository settings:
* `BLUESKY_API_KEY`
* `BLUESKY_USERNAME`
* `GH_MODELS_API_KEY`

## Contributing

Feedback and contributions are welcome! Just open an issue and let's discuss before you send a pull request. 

## Acknowledgements

We acknowledge the financial support by the Federal Ministry of Education and Research of Germany and by Sächsische Staatsministerium für Wissenschaft, Kultur und Tourismus in the programme Center of Excellence for AI-research „Center for Scalable Data Analytics and Artificial Intelligence Dresden/Leipzig", project identification number: ScaDS.AI
