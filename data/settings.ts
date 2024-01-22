import * as fs from "fs";

type SettingsType = { [key: string]: string };

function getLocalFile(serverId: string) {
    if (!fs.existsSync("datastore")) {
        fs.mkdirSync("datastore");
    }
    if (!fs.existsSync("datastore/settings")) {
        fs.mkdirSync("datastore/settings");
    }
    if (!fs.existsSync(`datastore/settings/${serverId}.json`)) {
        fs.writeFileSync(`datastore/settings/${serverId}.json`, "{}");
    }
    const file = fs.readFileSync(`datastore/settings/${serverId}.json`, "utf-8");
    return JSON.parse(file) as SettingsType;
}

function setLocalFile(serverId: string, data: SettingsType) {
    if (!fs.existsSync("datastore")) {
        fs.mkdirSync("datastore");
    }
    if (!fs.existsSync("datastore/settings")) {
        fs.mkdirSync("datastore/settings");
    }
    fs.writeFileSync(`datastore/settings/${serverId}.json`, JSON.stringify(data));
}

function getDefaultsFile(): { [key: string]: string | undefined } {
    if (!fs.existsSync("datastore")) {
        fs.mkdirSync("datastore");
    }
    if (!fs.existsSync("datastore/settings")) {
        fs.mkdirSync("datastore/settings");
    }
    if (!fs.existsSync("datastore/settings/default.json")) {
        fs.writeFileSync("datastore/settings/default.json", "{}");
    }
    return JSON.parse(fs.readFileSync("datastore/settings/default.json", "utf-8")) as {
        [key: string]: string | undefined;
    };
}

function setDefaultsFile(data: { [key: string]: string | undefined }) {
    if (!fs.existsSync("datastore")) {
        fs.mkdirSync("datastore");
    }
    if (!fs.existsSync("datastore/settings")) {
        fs.mkdirSync("datastore/settings");
    }
    fs.writeFileSync("datastore/settings/default.json", JSON.stringify(data));
}

export function setSetting(serverId: string, key: string, value: string, defa: string = "") {
    const settings = getLocalFile(serverId);
    settings[key] = value;
    setLocalFile(serverId, settings);
}

export function getSetting(serverId: string, key: string): string {
    const settings = getLocalFile(serverId);
    if (!settings[key]) {
        const defaults = getDefaultsFile();
        settings[key] = defaults[key] ?? "";
        setLocalFile(serverId, settings);
    }
    return settings[key];
}

export function defaultSetting(key: string, defaul: string) {
    const settings = getDefaultsFile();
    settings[key] = defaul;
    setDefaultsFile(settings);
}
