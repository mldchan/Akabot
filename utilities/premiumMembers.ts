import * as fs from "fs";

function readPremiumMembers(): string[] {
    if (!fs.existsSync("datastore")) fs.mkdirSync("datastore");
    if (!fs.existsSync("datastore/premiumMembers.json")) fs.writeFileSync("datastore/premiumMembers.json", "[]");
    return JSON.parse(fs.readFileSync("datastore/premiumMembers.json").toString());
}

export function isMemberPremium(id: string) {
    return readPremiumMembers().includes(id);
}
