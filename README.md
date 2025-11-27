# Brain Box
A note-taking app which allows you to create notes under topics or sub-topics, it comes with an offline-first PWA which enables
you to use it on wide range of devices.

The aim of the project is to create an uncluttered, cross-platform, light-weight and locally self-hostable note-taking app.

## The Stack
The main technologies used to build this application are:
- FastAPI
- SQLite
- React
- Tanstack Query

## Current Limitations
- *General:* This project is meant to be used in a local self-hosted environment for now.
- *PWA:* For it to be usable as an offline-first PWA it needs you to install self-signed certificates on devices which you use it on.
- *PWA:* In order for it to sync your notes to the backend(this repo) you need to open the PWA app when online.
- *PWA:* Currently only supports offline note creation, topics cannot be created offline as of now.
