import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction, Client, EmbedBuilder,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    SlashCommandBuilder,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "@/modules/type";
import * as fs from "fs";
import { getToday } from "@/utilities/dates";

type Streak = {
    startDate: number, lastMessageDate: number
}

function streakReadFile(guildID: string, userID: string): Streak {
    if (!fs.existsSync(`data/${guildID}`)) fs.mkdirSync(`data/${guildID}`);
    if (!fs.existsSync(`data/${guildID}/${userID}streak.json`)) fs.writeFileSync(`data/${guildID}/${userID}streak.json`, JSON.stringify({
        startDate: getToday().getTime(), lastMessageDate: getToday().getTime()
    }));
    return JSON.parse(fs.readFileSync(`data/${guildID}/${userID}streak.json`, "utf-8"));
}

function streakWriteFile(guildID: string, memberID: string, data: Streak) {
    fs.writeFileSync(`data/${guildID}/${memberID}streak.json`, JSON.stringify(data));
}

function updateStreak(msg: Message<boolean>) {
    if (!msg.guild) return;
    const d = new Date();
    d.setUTCHours(0);
    d.setUTCMinutes(0);
    d.setUTCSeconds(0);
    const data = streakReadFile(msg.guild.id, msg.author.id);
    if (getToday().getTime() - data.lastMessageDate > 48 * 3600 * 1000) {
        data.startDate = getToday().getTime();
    }
    data.lastMessageDate = getToday().getTime();
    streakWriteFile(msg.guild.id, msg.author.id, data);
}

function getStreakStatus(guildID: string, memberID: string) {
    const data = streakReadFile(guildID, memberID);
    return {
        expired: getToday().getTime() - data.lastMessageDate > 48 * 3600 * 1000,
        days: Math.floor((getToday().getTime() - data.startDate) / (24 * 3600 * 1000)) + 1,
        messageTimeDiff: getToday().getTime() - data.lastMessageDate
    };
}

export class ChatStreakModule implements Module {
    commands: AllCommands = [new SlashCommandBuilder()
        .setName("streak")
        .setDescription("See what your current chat streak is.")];
    selfMemberId: string = "";

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
        if (interaction.commandName !== "streak") return;
        if (!interaction.guild) return;
        const streakStatus = getStreakStatus(interaction.guild.id, interaction.user.id);
        const plural = streakStatus.days == 1 ? "" : "s";

        const embed = new EmbedBuilder()
            .setTitle("Streak Status")
            .setFields([
                {name: "Current", value: `${streakStatus.days} day${plural}`}
            ]);

        await interaction.reply({embeds: [embed], ephemeral: true});
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
        const streakStatus = getStreakStatus(msg.guild!.id, msg.author.id);
        console.log("streakMessage days", streakStatus.days);
        console.log("streakMessage timeDiff", streakStatus.messageTimeDiff);
        updateStreak(msg);
        const streakStatusAfter = getStreakStatus(msg.guild!.id, msg.author.id);
        console.log("streakMessage afterDays", streakStatusAfter.days);

        if (streakStatus.expired) {
            msg.channel.send(`Your streak of ${streakStatus.days} consecutive days of sending a message has expired :c\nYou now have 1 day streak.`);
        } else if (streakStatus.messageTimeDiff > 24 * 3600 * 1000 && streakStatusAfter.messageTimeDiff < 48 * 3600 * 1000) {
            msg.channel.send(`${streakStatusAfter.days} consecutive days of you sending a message! Keep it going :3`);
        }
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
    async onReady(client: Client): Promise<void> {}
}
