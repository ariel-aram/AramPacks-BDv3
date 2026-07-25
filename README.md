# Aram Packs for Ballsdex v3

This is a collection of extras (packages) for Ballsdex v3, taken from old packages that were used in previous versions of Ballsdex and now fully migrated to Ballsdex v3.

In order to use these extras, please copy the contents from the `extra` directory and paste it on the `extra` directory of your Ballsdex v3 installation, then configure `extra.toml` on your `config` directory.

## Shell

```bash
# Change /path/to/ballsdex to your Ballsdex v3 installation path.
cp -r extra/* /path/to/ballsdex/extra/
cp config/extra.toml /path/to/ballsdex/config/extra.toml
```

## PowerShell

```powershell
# Change $BDV3_PATH to your Ballsdex v3 installation path.
Copy-Item -Path .\extra\* -Destination "$BDV3_PATH\extra" -Recurse -Force
Copy-Item -Path .\config\extra.toml -Destination "$BDV3_PATH\config\extra.toml" -Force
```

## Batch

```cmd
REM Change %BDV3_PATH% to your Ballsdex v3 installation path.
xcopy /E /I /Y extra\* "%BDV3_PATH%\extra"
copy /Y config\extra.toml "%BDV3_PATH%\config\extra.toml"
```

After you copy the necessary files from this repository into your Ballsdex v3 installation, feel free to configure `extra.toml` to your own liking.

Then lastly, run the following command to restart the bot and load the extras.

```bash
docker compose up -d --build
```

The original creators behind almost all the extras in this repository are **Haymooed**, **Caylies**, and **molteencreates**. Therefore, all credits go to them.
