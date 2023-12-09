import {
    ChatInputCommandInteraction,
    CacheType,
    ButtonInteraction,
    Role,
    Channel,
    Message,
    GuildMember,
    Guild,
    Emoji,
    Sticker, SlashCommandBuilder
} from "discord.js";
import { AllCommands, Module } from "./type";
import * as fs from "fs";

type Streak = {
    startDate: number,
    lastMessageDate: number
}

function streakReadFile(guildID: string, userID: string): Streak {
    if (!fs.existsSync(`data/${guildID}`)) fs.mkdirSync(`data/${guildID}`);
    if(!fs.existsSync(`data/${guildID}/${userID}streak.json`)) fs.writeFileSync(`data/${guildID}/${userID}streak.json`, JSON.stringify({
        startDate: Date.now(),
        lastMessageDate: Date.now()
    }));
    return JSON.parse(fs.readFileSync(`data/${guildID}/${userID}streak.json`, "utf-8"));
}

function streakWriteFile(guildID: string, memberID: string, data: Streak) {
    fs.writeFileSync(`data/${guildID}/${memberID}streak.json`, JSON.stringify(data));
}

function updateStreak(msg: Message<boolean>) {
    if (!msg.guild) return;
    const data = streakReadFile(msg.guild.id, msg.author.id);
    if (Date.now() - data.lastMessageDate > 48 * 3600 * 1000) {
        data.startDate = Date.now()
    }
    data.lastMessageDate = Date.now()
    streakWriteFile(msg.guild.id, msg.author.id, data);
}

function getStreakStatus(guildID: string, memberID: string) {
    const data = streakReadFile(guildID, memberID);
    return {
        expired: Date.now() - data.lastMessageDate > 48 * 3600 * 1000,
        days: Math.floor((Date.now() - data.startDate) / (24 * 3600 * 1000)),
        messageTimeDiff: Date.now() - data.lastMessageDate,
        expiresIn: {
            hours: Math.floor((48 * 3600 * 1000 - (Date.now() - data.lastMessageDate)) / 3600 / 1000),
            minutes: Math.floor((48 * 3600 * 1000 - (Date.now() - data.lastMessageDate)) / 60 / 1000) % 60,
        }
    }
}

export class ChatStreakModule implements Module {
    async onEmojiCreate(emoji: Emoji): Promise<void> {}
    async onEmojiDelete(emoji: Emoji): Promise<void> {}
    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {}
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    commands: AllCommands = [
        new SlashCommandBuilder()
            .setName("streak")
            .setDescription("See what your current chat streak is.")
    ];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (interaction.commandName !== "streak") return;
        if (!interaction.guild) return;
        const streakStatus = getStreakStatus(interaction.guild.id, interaction.user.id);
        await interaction.reply({
            content: `# Streak Status
- **Current**: ${streakStatus.days} days
- Expires in ${streakStatus.expiresIn.hours} hours and ${streakStatus.expiresIn.minutes} minutes
- **Send a chat message to renew :3**`,
            ephemeral: true
        })
    }
    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}
    async onRoleCreate(role: Role): Promise<void> {}
    async onRoleEdit(before: Role, after: Role): Promise<void> {}
    async onRoleDelete(role: Role): Promise<void> {}
    async onChannelCreate(role: Channel): Promise<void> {}
    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}
    async onChannelDelete(role: Channel): Promise<void> {}
    async onMessage(msg: Message<boolean>): Promise<void> {
        const streakStatus = getStreakStatus(msg.guild!.id, msg.author.id);
        updateStreak(msg);
        const streakStatusAfter = getStreakStatus(msg.guild!.id, msg.author.id);

        if (streakStatus.expired) {
            msg.channel.send(`Your streak of ${streakStatus.days} days has expired :c`)
        }
        else if (streakStatus.messageTimeDiff > 24 * 3600 * 1000 && streakStatusAfter.messageTimeDiff < 48 * 3600 * 1000) {
            msg.channel.send(`${streakStatusAfter.days} days of streak! Keep it going :3`)
        }
    }
    async onMessageDelete(msg: Message<boolean>): Promise<void> {}
    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {}
    async onMemberJoin(member: GuildMember): Promise<void> {}
    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}
    async onMemberLeave(member: GuildMember): Promise<void> {}
    async onGuildAdd(guild: Guild): Promise<void> {}
    async onGuildRemove(guild: Guild): Promise<void> {}
    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}
}
