import * as fs from "fs";

type SettingsType = { [key: string]: string };

function getLocalFile(serverId: string) {
  if (!fs.existsSync("data")) {
    fs.mkdirSync("data");
  }
  if (!fs.existsSync("data/settings")) {
    fs.mkdirSync("data/settings");
  }
  if (!fs.existsSync(`data/settings/${serverId}.json`)) {
    fs.writeFileSync(`data/settings/${serverId}.json`, "{}");
  }
  const file = fs.readFileSync(`data/settings/${serverId}.json`, "utf-8");
  return JSON.parse(file) as SettingsType;
}

function setLocalFile(serverId: string, data: SettingsType) {
  if (!fs.existsSync("data")) {
    fs.mkdirSync("data");
  }
  if (!fs.existsSync("data/settings")) {
    fs.mkdirSync("data/settings");
  }
  fs.writeFileSync(`data/settings/${serverId}.json`, JSON.stringify(data));
}

function getGlobalSettings() {
  if (!fs.existsSync("data")) {
    fs.mkdirSync("data");
  }
  if (!fs.existsSync("data/settings")) {
    fs.mkdirSync("data/settings");
  }
  if (!fs.existsSync(`data/settings/global.json`)) {
    fs.writeFileSync(`data/settings/global.json`, "{}");
  }
  const file = fs.readFileSync(`data/settings/global.json`, "utf-8");
  return JSON.parse(file) as SettingsType;
}

function setGlobalSettings(data: SettingsType) {
  if (!fs.existsSync("data")) {
    fs.mkdirSync("data");
  }
  if (!fs.existsSync("data/settings")) {
    fs.mkdirSync("data/settings");
  }
  fs.writeFileSync(`data/settings/global.json`, JSON.stringify(data));
}

export function setSetting(
  serverId: string,
  key: string,
  value: string,
  defa: string = ""
) {
  const settings = getLocalFile(serverId);
  settings[key] = value;
  setLocalFile(serverId, settings);
}

export function getSetting(
  serverId: string,
  key: string,
  defaul: string
): string {
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
