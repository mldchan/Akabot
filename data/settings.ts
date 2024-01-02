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

function getGlobalSettings() {
    if (!fs.existsSync("datastore")) {
        fs.mkdirSync("datastore");
    }
    if (!fs.existsSync("datastore/settings")) {
        fs.mkdirSync("datastore/settings");
    }
    if (!fs.existsSync(`datastore/settings/global.json`)) {
        fs.writeFileSync(`datastore/settings/global.json`, "{}");
    }
    const file = fs.readFileSync(`datastore/settings/global.json`, "utf-8");
    return JSON.parse(file) as SettingsType;
}

function setGlobalSettings(data: SettingsType) {
    if (!fs.existsSync("datastore")) {
        fs.mkdirSync("datastore");
    }
    if (!fs.existsSync("datastore/settings")) {
        fs.mkdirSync("datastore/settings");
    }
    fs.writeFileSync(`datastore/settings/global.json`, JSON.stringify(data));
}

export function setSetting(serverId: string, key: string, value: string, defa: string = "") {
    const settings = getLocalFile(serverId);
    settings[key] = value;
    setLocalFile(serverId, settings);
}

export function getSetting(serverId: string, key: string, defaul: string): string {
    const settings = getLocalFile(serverId);
    if (!settings[key]) {
        settings[key] = defaul;
        setLocalFile(serverId, settings);
    }
    return settings[key];
}

export function setGlobalSetting(key: string, value: string) {
    const settings = getGlobalSettings();
    settings[key] = value;
    setGlobalSettings(settings);
}

export function getGlobalSetting(key: string, defaul: string): string {
    const settings = getGlobalSettings();
    if (!settings[key]) {
        settings[key] = defaul;
        setGlobalSettings(settings);
    }
    return settings[key];
}
