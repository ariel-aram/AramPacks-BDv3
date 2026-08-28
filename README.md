# AramPacks for Ballsdex v3

This is a collection of extras (packages) for Ballsdex v3, taken from old packages that were used in previous versions of Ballsdex and now fully migrated to Ballsdex v3.

In order to use these extras, please copy the contents from the `extra` directory and paste it on the `extra` directory of your Ballsdex v3 installation, then configure `extra.toml` on your `config` directory.

## Copy and Configure

```bash
# Change /path/to/ballsdex to your Ballsdex v3 installation path.
cp config/extra.toml /path/to/ballsdex/config/extra.toml
```

After you copy `extra.toml` from this repository into your Ballsdex v3 installation, feel free to configure it to your own liking.

## Rebuild and Restart

```bash
docker compose up -d --build
```

## Credits

The original creators behind almost all the extras in this repository are **Haymooed**, **Caylies**, and **molteencreates**. Therefore, all credits go to them. Only one of the packages in here are owned by me, **ariel-aram**.
