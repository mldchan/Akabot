import * as fs from "fs";

function readBlockedFile(): { servers: string[]; users: string[] } {
    if (!fs.existsSync("datastore")) fs.mkdirSync("datastore");
    if (!fs.existsSync("datastore/blocked.json"))
        fs.writeFileSync("datastore/blocked.json", JSON.stringify({ servers: [], users: [] }));
    return JSON.parse(fs.readFileSync("datastore/blocked.json", "utf8"));
}

export function isServerBlocked(id: string): boolean {
    const data = readBlockedFile();
    return data.servers.map((x: any) => x.toString()).includes(id);
}

export function isUserBlocked(id: string): boolean {
    const data = readBlockedFile();
    return data.users.map((x: any) => x.toString()).includes(id);
}
