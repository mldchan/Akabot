import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction,
    Client,
    EmbedBuilder,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    SlashCommandBuilder,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import * as fs from "fs";
import { isMemberPremium } from "../utilities/premiumMembers";
import { getToday } from "../utilities/dates";

type Streak = {
    startDate: number;
    lastMessageDate: number;
};

function streakReadFile(guildID: string, userID: string): Streak {
    if (!fs.existsSync(`datastore`)) fs.mkdirSync(`datastore`);
    if (!fs.existsSync(`datastore/chatstreak`)) fs.mkdirSync(`datastore/chatstreak`);
    if (!fs.existsSync(`datastore/chatstreak/${guildID}`)) fs.mkdirSync(`datastore/chatstreak/${guildID}`);
    if (!fs.existsSync(`datastore/chatstreak/${guildID}/${userID}.json`))
        fs.writeFileSync(
            `datastore/chatstreak/${guildID}/${userID}.json`,
            JSON.stringify({
                startDate: getToday().getTime(),
                lastMessageDate: new Date().getTime()
            })
        );
    return JSON.parse(fs.readFileSync(`datastore/chatstreak/${guildID}/${userID}.json`, "utf-8"));
}

function streakWriteFile(guildID: string, memberID: string, data: Streak) {
    if (!fs.existsSync(`datastore`)) fs.mkdirSync(`datastore`);
    if (!fs.existsSync(`datastore/chatstreak`)) fs.mkdirSync(`datastore/chatstreak`);
    if (!fs.existsSync(`datastore/chatstreak/${guildID}`)) fs.mkdirSync(`datastore/chatstreak/${guildID}`);
    fs.writeFileSync(`datastore/chatstreak/${guildID}/${memberID}.json`, JSON.stringify(data));
}

function updateStreak(msg: Message<boolean>) {
    if (!msg.guild) return;
    let data = streakReadFile(msg.guild.id, msg.author.id);
    if (new Date().getTime() - data.lastMessageDate > 48 * 3600000 && !isMemberPremium(msg.author.id)) {
        data.startDate = getToday().getTime();
    }
    data.lastMessageDate = new Date().getTime();
    streakWriteFile(msg.guild.id, msg.author.id, data);
}

function getStreakStatus(guildID: string, memberID: string) {
    const data = streakReadFile(guildID, memberID);

    if (isMemberPremium(memberID)) {
        return {
            expired: false,
            days: Math.floor((getToday().getTime() - data.startDate) / (24 * 3600 * 1000)) + 1,
            messageTimeDiff: new Date().getTime() - data.lastMessageDate,
            lastMessageDate: data.lastMessageDate
        };
    }

    return {
        expired: new Date().getTime() - data.lastMessageDate > 48 * 3600 * 1000,
        days: Math.floor((new Date().getTime() - data.startDate) / (24 * 3600 * 1000)) + 1,
        messageTimeDiff: new Date().getTime() - data.lastMessageDate,
        lastMessageDate: data.lastMessageDate
    };
}

function getMemberSilenceStatus(memberId: string) {
    if (!fs.existsSync(`datastore`)) fs.mkdirSync(`datastore`);
    if (!fs.existsSync(`datastore/chatstreak`)) fs.mkdirSync(`datastore/chatstreak`);
    if (!fs.existsSync(`datastore/chatstreak/silence.json`))
        fs.writeFileSync(`datastore/chatstreak/silence.json`, "{}");
    const data = JSON.parse(fs.readFileSync(`datastore/chatstreak/silence.json`, "utf-8"));
    return data[memberId] ? data[memberId] : false;
}

function setMemberSilenceStatus(memberId: string, status: boolean) {
    if (!fs.existsSync(`datastore`)) fs.mkdirSync(`datastore`);
    if (!fs.existsSync(`datastore/chatstreak`)) fs.mkdirSync(`datastore/chatstreak`);
    if (!fs.existsSync(`datastore/chatstreak/silence.json`))
        fs.writeFileSync(`datastore/chatstreak/silence.json`, "{}");
    const data = JSON.parse(fs.readFileSync(`datastore/chatstreak/silence.json`, "utf-8"));
    data[memberId] = status;
    fs.writeFileSync(`datastore/chatstreak/silence.json`, JSON.stringify(data));
}

export class ChatStreakModule implements Module {
    commands: AllCommands = [
        new SlashCommandBuilder().setName("streak").setDescription("See what your current chat streak is.")
    ];
    selfMemberId: string = "";

    async onEmojiCreate(emoji: Emoji): Promise<void> {}

    async onEmojiDelete(emoji: Emoji): Promise<void> {}

    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}

    async onStickerCreate(sticker: Sticker): Promise<void> {}

    async onStickerDelete(sticker: Sticker): Promise<void> {}

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        switch (interaction.commandName) {
            case "streak": {
                if (!interaction.guild) return;
                const streakStatus = getStreakStatus(interaction.guild.id, interaction.user.id);
                const plural = streakStatus.days == 1 ? "" : "s";

                const embed = new EmbedBuilder()
                    .setTitle("Streak Status")
                    .setFields([{ name: "Current", value: `${streakStatus.days} day${plural}` }]);

                await interaction.reply({ embeds: [embed], ephemeral: true });
                break;
            }
            case "settings": {
                const subCommandGroup = interaction.options.getSubcommandGroup(false);
                if (subCommandGroup !== "chatstreak") break;
                const subCommand = interaction.options.getSubcommand(false);
                if (subCommand !== "status-message") break;
                const newStatus = interaction.options.getBoolean("enabled", true);
                setMemberSilenceStatus(interaction.user.id, newStatus);

                await interaction.reply({
                    content: newStatus ? "Streak messages are now unsilenced." : "Streak messages are now silenced.",
                    ephemeral: true
                });
                break;
            }
        }
    }

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}

    async onRoleCreate(role: Role): Promise<void> {}

    async onRoleEdit(before: Role, after: Role): Promise<void> {}

    async onRoleDelete(role: Role): Promise<void> {}

    async onChannelCreate(role: Channel): Promise<void> {}

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}

    async onChannelDelete(role: Channel): Promise<void> {}

    async onMessage(msg: Message<boolean>): Promise<void> {
        if (!msg.guild) return;
        if (msg.author.bot) return;
        const streakStatus = getStreakStatus(msg.guild.id, msg.author.id);

        updateStreak(msg);

        const streakStatusAfter = getStreakStatus(msg.guild.id, msg.author.id);

        if (streakStatus.expired) {
            msg.channel.send(
                `Your streak of ${streakStatus.days} consecutive days of sending a message has expired :c\nYou now have 1 day streak.`
            );
        } else if (streakStatus.messageTimeDiff > 43200000) {
            if (getMemberSilenceStatus(msg.author.id)) {
                msg.channel.send(
                    `${streakStatusAfter.days} consecutive days of you sending a message! Keep it going :3`
                );
            }
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
    async onReady(client: Client): Promise<void> {}
}
