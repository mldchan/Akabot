import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction, Client,
    Emoji,
    Guild, GuildBasedChannel, GuildChannel,
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

function readSettingsFile(guildID: string): TheType[] {
    if (!fs.existsSync(`data/${guildID}`)) fs.mkdirSync(`data/${guildID}`);
    if (!fs.existsSync(`data/${guildID}/revivalsettings.json`)) fs.writeFileSync(`data/${guildID}/revivalsettings.json`, JSON.stringify([]));
    return JSON.parse(fs.readFileSync(`data/${guildID}/revivalsettings.json`, "utf-8"));
}

function writeSettingsFile(guildID: string, data: TheType[]) {
    fs.writeFileSync(`data/${guildID}/revivalsettings.json`, JSON.stringify(data));
}

function setChannel(guildID: string, channelID: string, triggerTime: number) {
    const data = readSettingsFile(guildID);
    const index = data.findIndex((v: TheType) => v.id === channelID);
    if (index === -1) {
        data.push({ id: channelID, lastMessageTime: Date.now(), triggerTime, hasBeenTriggered: false });
    } else {
        data[index].triggerTime = triggerTime;
    }
    writeSettingsFile(guildID, data);
}

function removeChannel(guildID: string, channelID: string) {
    const data = readSettingsFile(guildID);
    const index = data.findIndex((v: TheType) => v.id === channelID);
    if (index === -1) return;
    data.splice(index, 1);
    writeSettingsFile(guildID, data);
}

function updateChannelLastSentMessage(channel: If<boolean, GuildTextBasedChannel, TextBasedChannel>) {
    if (channel.isDMBased()) return;
    const data = readSettingsFile(channel.guild.id);
    const channel2 = data.find((v: TheType) => v.id === channel.id);
    if (!channel2) return;
    channel2.lastMessageTime = Date.now();
    channel2.hasBeenTriggered = false;
    writeSettingsFile(channel.guild.id, data);
}

function checkTime(channel: If<boolean, GuildTextBasedChannel, TextBasedChannel>) {
    if (channel.isDMBased()) return;
    const data = readSettingsFile(channel.guild.id);
    const channel2 = data.find((v: TheType) => v.id === channel.id);
    if (!channel2) return;
    console.log(Date.now() - channel2.lastMessageTime, "since last message");
    if (Date.now() - channel2.lastMessageTime > channel2.triggerTime) {
        channel.send("This channel has been inactive for a while. Revive it by sending a message!");
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
    }
}

export class ChatReviveModule implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";
    selfMember: User | null = null;

    async onEmojiCreate(emoji: Emoji): Promise<void> {
    }

    async onEmojiDelete(emoji: Emoji): Promise<void> {
    }

    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {
    }

    async onStickerCreate(sticker: Sticker): Promise<void> {
    }

    async onStickerDelete(sticker: Sticker): Promise<void> {
    }

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {
    }

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (!interaction.guild) return;
        if (interaction.commandName !== "settings") return;
        const group = interaction.options.getSubcommandGroup(false);
        if (group !== "chatrevive") return;
        await handleSettingsCommand(interaction);
    }

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {
    }

    async onRoleCreate(role: Role): Promise<void> {
    }

    async onRoleEdit(before: Role, after: Role): Promise<void> {
    }

    async onRoleDelete(role: Role): Promise<void> {
    }

    async onChannelCreate(role: Channel): Promise<void> {
    }

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {
    }

    async onChannelDelete(role: Channel): Promise<void> {
    }

    async onMessage(msg: Message<boolean>): Promise<void> {
        if (msg.author.bot) return;
        updateChannelLastSentMessage(msg.channel);
    }

    async onMessageDelete(msg: Message<boolean>): Promise<void> {
    }

    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {
    }

    async onMemberJoin(member: GuildMember): Promise<void> {
    }

    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {
    }

    async onMemberLeave(member: GuildMember): Promise<void> {
    }

    async onGuildAdd(guild: Guild): Promise<void> {
    }

    async onGuildRemove(guild: Guild): Promise<void> {
    }

    async onGuildEdit(before: Guild, after: Guild): Promise<void> {
    }

    async onTick(): Promise<void> {
        console.log("chatRevive tick");
        if (!this.selfMember) return;
        for (const guild of this.selfMember.client.guilds.cache) {
            const data = readSettingsFile(guild[0]);
            for (const item of data) {
                const channel = guild[1].channels.cache.get(item.id);
                if (!channel) continue;
                if (!channel.isTextBased()) continue;
                checkTime(channel);
            }
        }
    }
    async onReady(client: Client): Promise<void> {
        this.selfMember = client.user;
    }
}
