import * as fs from "fs";

type UserData = {
  xp: number;
};

function getFile(guildId: string, memberId: string) {
  if (!fs.existsSync("data")) fs.mkdirSync("data");
  if (!fs.existsSync(`data/${guildId}`)) fs.mkdirSync(`data/${guildId}`);
  if (!fs.existsSync(`data/${guildId}/${memberId}.json`)) {
    fs.writeFileSync(
      `data/${guildId}/${memberId}.json`,
      JSON.stringify({
        xp: 0,
      } as UserData)
    );
  }

  const data = fs.readFileSync(`data/${guildId}/${memberId}.json`, "utf-8");
  return JSON.parse(data) as UserData;
}

function setFile(guildId: string, memberId: string, data: UserData) {
  if (!fs.existsSync("data")) fs.mkdirSync("data");
  if (!fs.existsSync(`data/${guildId}`)) fs.mkdirSync(`data/${guildId}`);
  fs.writeFileSync(
    `data/${guildId}/${memberId}.json`,
    JSON.stringify(data as UserData)
  );
}

export function addPointsToUser(
  guildId: string,
  memberId: string,
  points: number
) {
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
