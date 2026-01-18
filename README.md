# Easydict Alfred Workflow

Use the power of Easydict in Alfred! Look up words and translate text easily with multiple services.

Based on the excellent [Raycast Easydict](https://github.com/tisfeng/Raycast-Easydict).

## Features

- **Dictionary Lookup**: Rich results with definitions, phonetics, and word forms.
- **Smart Translation**: Parallel translation using multiple services.
- **Auto-Fallback**: Tries free services (DeepLX, Youdao, Bing) automatically.
- **Audio Playback**: Hear pronunciations for words and sentences.
- **Customizable**: Enable/disable services and set your preferred languages.

## Installation

1. Download the latest `.alfredworkflow` file.
2. Double-click to install in Alfred.
3. (Optional) Python 3 is required (usually pre-installed on macOS).

## Usage

### Dictionary (`di`)

Type `di` followed by a word to look it up.

```
di good
```

- **Enter**: Copy the definition.
- **⌥ + Enter**: Play pronunciation.
- **⌘ + Enter**: Open in Eudic (if installed).

### Translation (`tr`)

Type `tr` followed by a sentence to translate it.

```
tr Hello world
```

- **Enter**: Copy the translation.
- **⌥ + Enter**: Speak the translation (TTS).

## Configuration

You can configure the workflow in Alfred's "Workflow Configuration" panel (click the `[x]` icon in the top right).

### Services
- **Youdao Translate**: (Default) High-quality free translation.
- **DeepLX**: Free DeepL translation. *Note: Requires a custom endpoint in settings.*
- **Bing**: Free Microsoft translation.
- **Google**: Free Google translation (requires proxy in some regions).
- **DeepL / OpenAI**: (Coming soon) API key support.

### Languages
Set your primary and secondary languages ("First Language" and "Second Language") to control auto-detection and target language.

## Credits

- Original idea and implementation for Raycast: [tisfeng](https://github.com/tisfeng)
- Ported to Alfred by **oe/Antigravity**
