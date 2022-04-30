# Create a library

Use the `create_library` command to create new libraries for a given user.

```{list-table}
:header-rows: 1

* - Parameter
   - Data type
   - Description

* - `username`*
   - String
   - The user you want to create the library for.

* - `--name`
   - String
   - The name of the library. Defaults to "default".

* - `--privacy-level`
   - Enum (String)
   - The [privacy level](../../user_documentation/libraries/create_library.md) of the library  
      - `"me"` (default)
      - `"instance"`
      - `"everyone"`

```

## Examples

### Create a new library

Use the following command to create a new library with a custom name and privacy level.

::::{tab-set}

:::{tab-item} Debian
:sync: debian

```{code-block} bash
poetry run python manage.py create_library username1 --name="Library 1" --privacy-level="everyone"
```

:::

:::{tab-item} Docker
:sync: docker

```{code-block} bash
docker-compose run --rm api python manage.py create_library username1 --name="Library 1" --privacy-level="everyone"
```

:::

::::

### Returns

```{code-block} text-output
Created library Library 1 for user username1 with UUID 436da05b-8cb1-4a4d-b870-4a3b235d8517
```

### Create a new library wth no name or privacy level

You can create a library using only a username. The script substitutes default values for the library name and privacy level.

::::{tab-set}

:::{tab-item} Debian
:sync: debian

```{code-block} bash
poetry run python manage.py create_library username1
```

:::

:::{tab-item} Docker
:sync: docker

```{code-block} bash
docker-compose run --rm api python manage.py create_library username1
```

:::

::::

### Returns

```{code-block} text-output
Created library default for user username1 with UUID 436da05b-8cb1-4a4d-b870-4a3b235d8517
```

### Library with the same name already exists

If a library with the same name already exists for the given user, the script will __not__ create a new library.

::::{tab-set}

:::{tab-item} Debian
:sync: debian

```{code-block} bash
poetry run python manage.py create_library username1 --name="Library 1" --privacy-level="everyone"
```

:::

:::{tab-item} Docker
:sync: docker

```{code-block} bash
docker-compose run --rm api python manage.py create_library username1 --name="Library 1" --privacy-level="everyone"
```

:::

::::

### Returns

```{code-block} text-output
Found existing library Library 1 for user username1 with UUID 436da05b-8cb1-4a4d-b870-4a3b235d8517
```