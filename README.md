# Aram Packs for Ballsdex v3

This is a collection of extras (packages) for Ballsdex v3, taken from old packages that were used in previous versions of Ballsdex and now fully migrated to Ballsdex v3.

In order to use these extras, please copy the contents from the `extra` directory and paste it on the `extra` directory of your Ballsdex v3 installation, then configure `extra.toml` on your `config` directory.

```bash
# Change /path/to/ballsdex to your Ballsdex v3 installation path.
cp /path/to/BDv3AramExtras/extra/* /path/to/ballsdex/extra/
cp /path/to/BDv3AramExtras/config/extra.toml /path/to/ballsdex/config/extra.toml
```

After you copy the necessary files from this repository into your Ballsdex v3 installation, feel free to configure `extra.toml` to your own liking.

Then lastly, run the following command to restart the bot and load the extras.

```bash
docker compose up -d --build
```

The original creators behind most of the extras added into this repository are **Haymooed**, **Caylies**, and **molteencreates**. Therefore, credits go to them.
