import json
import requests
import logging
from datetime import datetime
import click

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Hardcode your GitHub token here for authentication with the GitHub API
GITHUB_TOKEN = ''


def get_latest_release_date(repo_url):
    """Fetch the latest release date from the GitHub API for a given repository."""
    repo_name = repo_url.replace("https://github.com/", "")
    api_url = f"https://api.github.com/repos/{repo_name}/releases/latest"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    try:
        logging.info(
            f"Checking for the latest release of the repository: {repo_name}")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes
        data = response.json()
        release_date = data.get("published_at", None)
        if release_date:
            # Format the release date as "Month Day, Year"
            formatted_date = datetime.strptime(
                release_date, "%Y-%m-%dT%H:%M:%SZ").strftime("%B %d, %Y")
            logging.info(
                f"Latest release date for {repo_name} is {formatted_date}.")
            return formatted_date
        else:
            # Handle case where no releases are found
            logging.warning(
                f"No releases found for {repo_name}. Setting release date as 'No releases'.")
            return "No releases"
    except requests.exceptions.HTTPError as e:
        logging.error(f"Failed to fetch the release date for {repo_name}: {e}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error while connecting to GitHub API: {e}")
    return "No releases"


def update_badges_json():
    """Update badges.json with the latest release dates."""
    with open('badges.json', 'r') as file:
        badges = json.load(file)

    updated_plugins = []

    for plugin in badges["plugins"]:
        repo_url = plugin["url"]
        current_release_date = plugin["releaseDate"]
        latest_release_date = get_latest_release_date(repo_url)

        if latest_release_date != current_release_date:
            # Update the release date if it's changed
            logging.info(
                f"Updating '{plugin['name']}' release date from {current_release_date} to {latest_release_date}.")
            plugin["releaseDate"] = latest_release_date
            updated_plugins.append(plugin["name"])

    if updated_plugins:
        # Write the updated release dates back to badges.json
        with open('badges.json', 'w') as file:
            json.dump(badges, file, indent=4)
        logging.info(
            "All release dates have been successfully updated in badges.json.")
    else:
        logging.info("No release dates needed updating in badges.json.")

    return updated_plugins


def update_readme(new_plugin):
    """Update the README.md file by adding the new plugin."""
    with open('badges.json', 'r') as file:
        badges = json.load(file)

    with open('README.md', 'r') as file:
        readme_content = file.read()

    # Find the location to insert the new plugin entry above <!-- END PLUGINS LIST -->
    insert_position = readme_content.find("<!-- END PLUGINS LIST -->")

    # Create the new plugin entry using the provided format
    index = len(badges["plugins"]) - 1
    new_entry = f"""
---

### [{new_plugin['name']}]({new_plugin['url']}) <br>

[![Latest Release Date](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Frusherdevelopment.github.io%2Frusherhack-plugins%2Fbadges.json&query=%24.plugins[{index}].releaseDate&label=Latest%20Release&color={new_plugin['color']})]({new_plugin['releaseUrl']}) ![GitHub Downloads (all releases)](https://img.shields.io/github/downloads/{new_plugin['url'].replace('https://github.com/', '')}/total)<br>

**Creator**: <img src="https://github.com/{new_plugin['url'].split('/')[-2]}.png?size=20" width="20" height="20"> [{new_plugin['url'].split('/')[-2]}](https://github.com/{new_plugin['url'].split('/')[-2]})
{new_plugin['description']}
"""

    # Insert the new plugin entry above <!-- END PLUGINS LIST -->
    readme_content = readme_content[:insert_position] + \
        new_entry + "\n" + readme_content[insert_position:]

    with open('README.md', 'w') as file:
        file.write(readme_content)

    logging.info(
        "README.md has been successfully updated with the new plugin.")


@click.group()
def cli():
    """Main entry point for the CLI tool."""
    pass


@cli.command()
@click.option('--repo_url', prompt='Enter the GitHub repository URL', help='The URL of the GitHub repository for the plugin.')
@click.option('--description', prompt='Enter the plugin description', help='A brief description of the plugin.')
def add(repo_url, description):
    """Add a new plugin to badges.json and README.md."""

    # Prompt for custom plugin state
    custom_state = click.prompt(
        "Enter a custom plugin state (e.g., In Development) or press Enter to fetch the latest release date",
        default="",
        show_default=False
    )

    logging.info(f"Preparing to add the new plugin: {repo_url}")

    if custom_state:
        # Use the custom state as the release date if provided
        logging.info(
            f"Custom plugin state '{custom_state}' will be used as the release date.")
        latest_release_date = custom_state
    else:
        # Fetch the latest release date from GitHub
        latest_release_date = get_latest_release_date(repo_url)

    with open('badges.json', 'r') as file:
        badges = json.load(file)

    # Create a dictionary for the new plugin
    new_plugin = {
        "name": repo_url.split("/")[-1],
        "url": repo_url,
        "releaseUrl": f"{repo_url}/releases",
        "releaseDate": latest_release_date,
        "color": "green" if latest_release_date != "No releases" else "yellow",
        "description": description
    }

    # Add the new plugin to the badges.json file
    badges["plugins"].append(new_plugin)

    with open('badges.json', 'w') as file:
        json.dump(badges, file, indent=4)

    logging.info(
        f"The new plugin '{new_plugin['name']}' has been successfully added to badges.json.")

    # Update the README file with the new plugin
    update_readme(new_plugin)


@cli.command()
def update():
    """Update badges.json and README.md with the latest release dates."""
    logging.info("Beginning the update process for all plugins...")
    updated_plugins = update_badges_json()
    if updated_plugins:
        logging.info("The following plugins have been updated:")
        for plugin in updated_plugins:
            logging.info(f"- {plugin}")
    else:
        logging.info("No plugins required updating.")


if __name__ == "__main__":
    # Run the CLI tool
    cli()
