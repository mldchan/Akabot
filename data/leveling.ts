import * as fs from "fs";

type UserData = {
    xp: number;
};

function getFile(guildId: string, memberId: string) {
    if (!fs.existsSync("datastore")) fs.mkdirSync("datastore");
    if (!fs.existsSync("datastore/leveling")) fs.mkdirSync("datastore/leveling");
    if (!fs.existsSync(`datastore/leveling/${guildId}`)) fs.mkdirSync(`datastore/leveling/${guildId}`);
    if (!fs.existsSync(`datastore/leveling/${guildId}/${memberId}.json`)) {
        fs.writeFileSync(
            `datastore/leveling/${guildId}/${memberId}.json`,
            JSON.stringify({
                xp: 0
            } as UserData)
        );
    }

    const data = fs.readFileSync(`datastore/leveling/${guildId}/${memberId}.json`, "utf-8");
    return JSON.parse(data) as UserData;
}

function setFile(guildId: string, memberId: string, data: UserData) {
    if (!fs.existsSync("datastore")) fs.mkdirSync("datastore");
    if (!fs.existsSync("datastore/leveling")) fs.mkdirSync("datastore/leveling");
    if (!fs.existsSync(`datastore/leveling/${guildId}`)) fs.mkdirSync(`datastore/leveling/${guildId}`);
    fs.writeFileSync(`datastore/leveling/${guildId}/${memberId}.json`, JSON.stringify(data as UserData));
}

export function addPointsToUser(guildId: string, memberId: string, points: number) {
    let data = getFile(guildId, memberId);
    data.xp += points;
    setFile(guildId, memberId, data);
}

export function getUserPoints(guildId: string, memberId: string): number {
    let data = getFile(guildId, memberId);
    return data.xp;
}

export function getUserLevel(points: number) {
    let nextLevelPoints = 500;
    let level = 1;
    while (points > nextLevelPoints) {
        level++;
        nextLevelPoints += 500 * level;
    }

    return level;
}

export function getUserRequirementForNextLevel(points: number) {
    let nextLevelPoints = 500;
    let level = 1;
    while (points > nextLevelPoints) {
        level++;
        nextLevelPoints += 500 * level;
    }

    return nextLevelPoints;
}
