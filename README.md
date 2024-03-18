# TwitchDownloader Automator

TD Automator is an extension for the TwitchDownloader CLI that creates a streamlined experience for downloading/rendering clips & chat with minimal input.  The program adds the functionality of combined automation for all steps of the process and prevents the undesired effect of chat videos starting empty when using a clip link to download.  Commands present in the program have been tailored to Windows systems, but could be altered to run in different environments.

## Installation

Below are steps taken directly from the TwitchDownloader github repository for the Windows installation.  If preferred, the Linux/MacOS installation process can be found [here](https://github.com/lay295/TwitchDownloader?tab=readme-ov-file#cli) (will require the modification of code).

### Twitch Downloader CLI & FFmpeg

1. Go to [Releases](https://github.com/lay295/TwitchDownloader/releases/) and download the latest version for Windows or [build from source](https://github.com/lay295/TwitchDownloader?tab=readme-ov-file#building-from-source).

2. Extract ```TwitchDownloaderCLI.exe```

3. Browse to where you extracted the executable:
```bash
cd C:\folder\containing\TwitchDownloaderCLI
```
4. If you do not have FFmpeg, you can install it via [Chocolatey package manager](https://community.chocolatey.org/), or you can get it as a standalone file from [ffmpeg.org](https://ffmpeg.org/download.html) or by using TwitchDownloaderCLI:
> Note: Python's subprocess module does not play nicely with FFmpeg depending on its installation location.  Due to this, TwitchDownloader CLI and FFmpeg should be inside the same folder.  The easiest way to do this is simply run the command below.
```bash
TwitchDownloaderCLI.exe ffmpeg --download
```

5. You can now start using TwitchDownloaderCLI, for example:
```bash
TwitchDownloaderCLI.exe videodownload --id <vod-id-here> -o out.mp4
```

You can find more example commands in the [CLI README](https://github.com/lay295/TwitchDownloader/blob/master/TwitchDownloaderCLI/README.md#example-commands).

### Twitch Developer Application

1. Follow the guidelines from this Twitch developers document for [registering your app](https://dev.twitch.tv/docs/authentication/register-app/).

2. Navigate to your Twitch developer console and store your **Client ID** and **Client Secret** somewhere easy to access later.

3. To get an access token, send an HTTP POST request to ```https://id.twitch.tv/oauth2/token```.  The following example shows the parameters in the body of the POST.
```
client_id=hof5gwx0su6owfnys0yan9c87zr6t
&client_secret=41vpdji4e9gif29md0ouet6fktd2
&grant_type=client_credentials
```

4. If the request succeeds, it returns an **access token**.  Also store this token somewhere easy to access later.
```
{
  "access_token": "jostpf5q0uzmxmkba9iyug38kjtgh",
  "expires_in": 5011271,
  "token_type": "bearer"
}
```

### General Dependencies

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install all dependencies.

```bash
pip install requirements.txt
```

## Usage

1. Run the program.
```bash
python TD-Automator.py
```

2. Select appropriate directories for each prompt.

3. Enter your **Client ID** and **access token** you obtained earlier.

## Contributing

Message hylight on discord for inquires.
