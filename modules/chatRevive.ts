import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction,
    Client,
    Emoji,
    Guild,
    GuildMember,
    GuildTextBasedChannel,
    If,
    Message,
    Role,
    Sticker,
    TextBasedChannel,
    User
} from "discord.js";
import { AllCommands, Module } from "./type";
import * as fs from "fs";

interface TheType {
    id: string;
    lastMessageTime: number;
    triggerTime: number; // ms
    hasBeenTriggered: boolean;
}

interface TheTheType {
    // naming doesn't exist
    roleID: string;
    things: TheType[];
}

function readSettingsFile(guildID: string): TheTheType {
    if (!fs.existsSync(`data/${guildID}`)) fs.mkdirSync(`data/${guildID}`);
    if (!fs.existsSync(`data/${guildID}/revivalsettings.json`))
        fs.writeFileSync(
            `data/${guildID}/revivalsettings.json`,
            JSON.stringify({
                roleID: "",
                things: []
            } as TheTheType)
        );
    return JSON.parse(fs.readFileSync(`data/${guildID}/revivalsettings.json`, "utf-8"));
}

function writeSettingsFile(guildID: string, data: TheTheType) {
    if (!fs.existsSync(`datastore`)) fs.mkdirSync(`datastore`);
    if (!fs.existsSync(`datastore/chatrevive`)) fs.mkdirSync(`datastore/chatrevive`);
    fs.writeFileSync(`datastore/chatrevive/${guildID}.json`, JSON.stringify(data));
}

function setChannel(guildID: string, channelID: string, triggerTime: number) {
    const data = readSettingsFile(guildID);
    const index = data.things.findIndex((v: TheType) => v.id === channelID);
    if (index === -1) {
        data.things.push({ id: channelID, lastMessageTime: Date.now(), triggerTime, hasBeenTriggered: false });
    } else {
        data.things[index].triggerTime = triggerTime;
    }
    writeSettingsFile(guildID, data);
}

function removeChannel(guildID: string, channelID: string) {
    const data = readSettingsFile(guildID);
    const index = data.things.findIndex((v: TheType) => v.id === channelID);
    if (index === -1) return;
    data.things.splice(index, 1);
    writeSettingsFile(guildID, data);
}

function updateChannelLastSentMessage(channel: If<boolean, GuildTextBasedChannel, TextBasedChannel>) {
    if (channel.isDMBased()) return;
    const data = readSettingsFile(channel.guild.id);
    const channel2 = data.things.find((v: TheType) => v.id === channel.id);
    if (!channel2) return;
    channel2.lastMessageTime = Date.now();
    channel2.hasBeenTriggered = false;
    writeSettingsFile(channel.guild.id, data);
}

function getRoleID(id: string) {
    const data = readSettingsFile(id);
    if (data.roleID === "" || data.roleID === "0") return undefined;
    return data.roleID;
}

function checkTime(channel: If<boolean, GuildTextBasedChannel, TextBasedChannel>) {
    if (channel.isDMBased()) return;
    const data = readSettingsFile(channel.guild.id);
    const channel2 = data.things.find((v: TheType) => v.id === channel.id);
    if (!channel2) return;
    const roleID = getRoleID(channel.guild.id);
    if (!roleID) return;
    console.log(Date.now() - channel2.lastMessageTime, "since last message");
    console.log(channel2.triggerTime - (Date.now() - channel2.lastMessageTime), "until revive");
    if (Date.now() - channel2.lastMessageTime > channel2.triggerTime) {
        if (channel2.hasBeenTriggered) return;
        channel.send(`<@&${roleID}> This channel has been inactive for a while. Revive it by sending a message!`);
        channel2.hasBeenTriggered = true;
        writeSettingsFile(channel.guild.id, data);
    }
}

async function handleSettingsCommand(interaction: ChatInputCommandInteraction) {
    if (!interaction.guild) return;
    const subcommand = interaction.options.getSubcommand(true);
    switch (subcommand) {
        case "set": {
            const chOpt = interaction.options.getChannel("channel", true);
            const ch = interaction.guild.channels.cache.get(chOpt.id);
            if (!ch) return;
            if (!ch.isTextBased()) {
                await interaction.reply({
                    content: "The channel must be a text channel.",
                    ephemeral: true
                });
                return;
            }
            const time = interaction.options.getNumber("time", true);
            setChannel(interaction.guild.id, ch.id, time * 60000);
            await interaction.reply({
                content: `Set channel <#${ch.id}> to auto-revive after ${time} minutes.`,
                ephemeral: true
            });
            break;
        }
        case "remove": {
            const ch = interaction.options.getChannel("channel", true);
            if (!ch) return;
            removeChannel(interaction.guild.id, ch.id);
            await interaction.reply({
                content: `Removed channel <#${ch.id}> from auto-revive.`,
                ephemeral: true
            });
            break;
        }
        case "role": {
            const role = interaction.options.getRole("role", true);
            const data = readSettingsFile(interaction.guild.id);
            data.roleID = role.id;
            writeSettingsFile(interaction.guild.id, data);
            await interaction.reply({
                content: `Set role <@&${role.id}> to be pinged when this channel is revived.`,
                ephemeral: true
            });
            break;
        }
    }
}

function hasSetPingRole(guild: Guild) {
    const data = readSettingsFile(guild.id);
    for (const item of data.things) {
        const channel = guild.channels.cache.get(item.id);
        if (!channel) continue;
        if (!channel.isTextBased()) continue;
        return true;
    }
    return false;
}

async function hasPermissions(interaction: ChatInputCommandInteraction<CacheType>) {
    //     check manage guild or admin
    if (!interaction.guild) return false;
    const member = interaction.guild.members.cache.get(interaction.user.id);
    if (!member) return false;
    if (!member.permissions.has("ManageGuild") && !member.permissions.has("Administrator")) {
        await interaction.reply({
            content: "You must have the Manage Server permission to use this command.",
            ephemeral: true
        });
        return false;
    }
    return true;
}

export class ChatReviveModule implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";
    selfMember: User | undefined = undefined;

    async onEmojiCreate(emoji: Emoji): Promise<void> {}

    async onEmojiDelete(emoji: Emoji): Promise<void> {}

    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}

    async onStickerCreate(sticker: Sticker): Promise<void> {}

    async onStickerDelete(sticker: Sticker): Promise<void> {}

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (!interaction.guild) return;
        if (interaction.commandName !== "settings") return;
        const group = interaction.options.getSubcommandGroup(false);
        if (group !== "chatrevive") return;
        if (!(await hasPermissions(interaction))) return;
        await handleSettingsCommand(interaction);
    }

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}

    async onRoleCreate(role: Role): Promise<void> {}

    async onRoleEdit(before: Role, after: Role): Promise<void> {}

    async onRoleDelete(role: Role): Promise<void> {}

    async onChannelCreate(role: Channel): Promise<void> {}

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}

    async onChannelDelete(role: Channel): Promise<void> {}

    async onMessage(msg: Message<boolean>): Promise<void> {
        if (msg.author.bot) return;
        updateChannelLastSentMessage(msg.channel);
    }

    async onMessageDelete(msg: Message<boolean>): Promise<void> {}

    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {}

    async onMemberJoin(member: GuildMember): Promise<void> {}

    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}

    async onMemberLeave(member: GuildMember): Promise<void> {}

    async onGuildAdd(guild: Guild): Promise<void> {}

    async onGuildRemove(guild: Guild): Promise<void> {}

    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}

    async onReady(client: Client): Promise<void> {
        setInterval(() => {
            for (const guild of client.guilds.cache.values()) {
                console.log("chatRevive tick checking", guild.name);
                const data = readSettingsFile(guild.id);
                if (!hasSetPingRole(guild)) continue;
                for (const item of data.things) {
                    const channel = guild.channels.cache.get(item.id);
                    if (!channel) continue;
                    console.log("checking", channel.name, "in", guild.name);
                    if (!channel.isTextBased()) continue;
                    checkTime(channel);
                }
            }
        }, 5000);
    }
}
