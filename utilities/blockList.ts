import * as fs from "fs";

// function readBlockedFile(): { servers: string[]; users: string[] } {
//     if (!fs.existsSync("datastore")) fs.mkdirSync("datastore");
//     if (!fs.existsSync("datastore/blocked.json"))
//         fs.writeFileSync("datastore/blocked.json", JSON.stringify({ servers: [], users: [] }));
//     return JSON.parse(fs.readFileSync("datastore/blocked.json", "utf8"));
// }

function readBlockedServersFile() {
    if (!fs.existsSync("datastore")) fs.mkdirSync("datastore");
    if (!fs.existsSync("datastore/blocklist")) fs.mkdirSync("datastore/blocklist");
    if (!fs.existsSync("datastore/blocklist/servers.csv")) fs.writeFileSync("datastore/blocklist/servers.csv", "");

    const read = fs.readFileSync("datastore/blocklist/servers.csv", "utf8");
    let servers = [] as { id: string; reason: string }[];

    read.split("\n").forEach((x) => {
        const split = x.split(";");
        if (split.length === 2) {
            servers.push({ id: split[0], reason: split[1] });
        }
    });

    return servers;
}

function readBlockedUsersFile() {
    if (!fs.existsSync("datastore")) fs.mkdirSync("datastore");
    if (!fs.existsSync("datastore/blocklist")) fs.mkdirSync("datastore/blocklist");
    if (!fs.existsSync("datastore/blocklist/users.csv")) fs.writeFileSync("datastore/blocklist/users.csv", "");

    const read = fs.readFileSync("datastore/blocklist/users.csv", "utf8");
    let users = [] as { id: string; reason: string }[];

    read.split("\n").forEach((x) => {
        const split = x.split(";");
        if (split.length === 2) {
            users.push({ id: split[0], reason: split[1] });
        }
    });

    return users;
}
export function isServerBlocked(id: string): false | string {
    const data = readBlockedServersFile();
    for (const iterator of data) {
        if (iterator.id === id) return iterator.reason;
    }
    return false;
}

export function isUserBlocked(id: string): false | string {
    const data = readBlockedUsersFile();
    for (const iterator of data) {
        if (iterator.id === id) return iterator.reason;            
    }
    return false;
}
