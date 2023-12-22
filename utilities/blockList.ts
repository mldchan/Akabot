import * as fs from "fs";

function readBlockedFile(): { servers: string[], users: string[] } {
    if (!fs.existsSync("./data/blocked.json"))
        fs.writeFileSync("./data/blocked.json", JSON.stringify({ servers: [], users: [] }));
    return JSON.parse(fs.readFileSync("./data/blocked.json", "utf8"));
}

export function isServerBlocked(id: string): boolean {
    const data = readBlockedFile();
    return data.servers.map((x: any) => x.toString()).includes(id);
}

export function isUserBlocked(id: string): boolean {
    const data = readBlockedFile();
    return data.users.map((x: any) => x.toString()).includes(id);
}
