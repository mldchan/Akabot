import * as fs from "fs";

export function isServerBlocked(id: string): boolean {
    if (!fs.existsSync("./data/blocked.json"))
        fs.writeFileSync("./data/blocked.json", JSON.stringify({ servers: [], users: [] }));
    const data = JSON.parse(fs.readFileSync("./data/blocked.json", "utf8"));
    return data.servers.map((x: any) => x.toString()).includes(id);
}

export function isUserBlocked(id: string): boolean {
    if (!fs.existsSync("./data/blocked.json"))
        fs.writeFileSync("./data/blocked.json", JSON.stringify({ servers: [], users: [] }));
    const data = JSON.parse(fs.readFileSync("./data/blocked.json", "utf8"));
    return data.users.map((x: any) => x.toString()).includes(id);
}
