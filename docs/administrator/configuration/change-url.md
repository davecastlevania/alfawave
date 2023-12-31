# Change your instance URL

```{danger}
We recommend you don't change your instance URL. Changing it __will__ cause instability and problems with federation. If you change your URL, the Funkwhale project can't offer support for problems that arise.
```

Your instance URL is your pod's unique identifier in the {term}`fediverse`. If you want to change it, you need to update a lot of information

- The instance URL in your {file}`.env` file.
- The instance URL in your webserver config.
- Any references to the old URL in your database.

To clean the database, the `funkwhale-manage` command line interface contains a `fix_federation_ids` command.

```{warning}
Running `fix_federation_ids` with the `--no-dry-run` flag is irreversible. Make sure you [back up your data](../upgrade/backup.md).
```

## Update your instance URL

1. Change the `FUNKWHALE_HOSTNAME` and `DJANGO_ALLOWED_HOSTS` value in your {file}`.env` file.
2. Change the `server_name` values in your {file}`/etc/nginx/sites-enabled/funkwhale.conf` file.
3. Run the `fix_federation_ids` command to clean up your database.

   ::::{tab-set}

   :::{tab-item} Debian
   :sync: debian

   ```{code-block} sh
   venv/bin/funkwhale-manage fix_federation_ids https://old-url https://new-url --no-dry-run --no-input
   ```

   :::

   :::{tab-item} Docker
   :sync: docker

   ```{code-block} sh
   sudo docker compose run --rm api funkwhale-manage fix_federation_ids https://old-url https://new-url --no-dry-run --no-input
   ```

   :::
   ::::

   Example output:

   ```{code-block} text
   Will replace 108 found occurrences of 'https://old-url' by 'https://new-url':

   - 20 music.Artist
   - 13 music.Album
   - 39 music.Track
   - 31 music.Upload
   - 1 music.Library
   - 4 federation.Actor
   - 0 federation.Activity
   - 0 federation.Follow
   - 0 federation.LibraryFollow

   Replacing on 20 music.Artist…
   Replacing on 13 music.Album…
   Replacing on 39 music.Track…
   Replacing on 31 music.Upload…
   Replacing on 1 music.Library…
   Replacing on 4 federation.Actor…
   Replacing on 0 federation.Activity…
   Replacing on 0 federation.Follow…
   Replacing on 0 federation.LibraryFollow…
   ```

4. Restart your webserver to pick up the changes.

   ::::{tab-set}

   :::{tab-item} Nginx
   :sync: nginx

   ```{code-block} sh
   sudo systemctl restart nginx
   ```

   :::

   :::{tab-item} Apache
   :sync: apache

   ```{code-block} sh
   sudo systemctl restart apache2
   ```

   :::
   ::::
