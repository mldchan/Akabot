import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction,
    Client,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "@/modules/type";
import * as fs from "fs";
import { getSelfMember } from "@/utilities/useful";

type DailyChatSummaryData = {
    channelID: string;
    messages: number;
    special: {
        owo: number;
        catface: number;
        meow: number;
    };
    users: {
        userID: string;
        messages: number;
    }[];
    lastSentDay: number;
    lastSentMonth: number;
};

function loadDailyChatSummary(guildId: string): DailyChatSummaryData[] {
    if (!fs.existsSync(`./data/${guildId}/dailyChatSummary.json`))
        fs.writeFileSync(`./data/${guildId}/dailyChatSummary.json`, JSON.stringify([]));
    const data = fs.readFileSync(`./data/${guildId}/dailyChatSummary.json`, "utf8");
    return JSON.parse(data);
}

function saveDailyChatSummary(guildId: string, data: DailyChatSummaryData[]) {
    fs.writeFileSync(`./data/${guildId}/dailyChatSummary.json`, JSON.stringify(data));
}

async function handleMessage(msg: Message<boolean>) {
    if (!msg.guild) return;
    const data = loadDailyChatSummary(msg.guild.id);
    const index = data.findIndex((v) => v.channelID === msg.channel.id);
    if (index === -1) return;
    data[index].messages++;

    const special = data[index].special;
    special.owo += msg.content.split("owo").length - 1;
    special.owo += msg.content.split("uwu").length - 1;

    special.catface += msg.content.split(":3").length - 1;

    special.meow += msg.content.split("meow").length - 1;
    special.meow += msg.content.split("nya").length - 1;

    const userIndex = data[index].users.findIndex((v) => v.userID === msg.author.id);
    if (userIndex === -1) {
        data[index].users.push({
            userID: msg.author.id,
            messages: 1
        });
    } else {
        data[index].users[userIndex].messages++;
    }

    saveDailyChatSummary(msg.guild.id, data);
}

async function settingsAddChannel(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;
    const channel = interaction.options.getChannel("channel", true);
    const data = loadDailyChatSummary(interaction.guild.id);
    const index = data.findIndex((v) => v.channelID === channel.id);
    if (index !== -1) {
        await interaction.reply({
            content: "That channel is already added",
            ephemeral: true
        });
        return;
    }
    data.push({
        channelID: channel.id,
        messages: 0,
        special: {
            owo: 0,
            catface: 0,
            meow: 0
        },
        users: [],
        lastSentDay: new Date().getDate(),
        lastSentMonth: new Date().getMonth()
    });
    await interaction.reply({
        content: "Added channel to daily chat summary, messages will be counted from now on",
        ephemeral: true
    });
    saveDailyChatSummary(interaction.guild.id, data);
}

async function settingsRemoveChannel(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;
    const channel = interaction.options.getChannel("channel", true);
    const data = loadDailyChatSummary(interaction.guild.id);
    const index = data.findIndex((v) => v.channelID === channel.id);
    if (index === -1) {
        await interaction.reply({
            content: "That channel is not added",
            ephemeral: true
        });
        return;
    }
    data.splice(index, 1);
    await interaction.reply({
        content: "Removed channel from daily chat summary",
        ephemeral: true
    });
    saveDailyChatSummary(interaction.guild.id, data);
}

async function handleSettingsCommands(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.memberPermissions) return;
    if (!interaction.memberPermissions.has("ManageGuild") || !interaction.memberPermissions.has("Administrator"))
        return;
    if (interaction.commandName !== "settings") return;
    const subcommandGroup = interaction.options.getSubcommandGroup(true);
    if (subcommandGroup !== "chatsummary") return;
    const subcommand = interaction.options.getSubcommand(true);
    switch (subcommand) {
        case "add-channel": {
            await settingsAddChannel(interaction);
            break;
        }
        case "remove-channel": {
            await settingsRemoveChannel(interaction);
            break;
        }
    }
}

async function checkDailyChatSummary(client: Client) {
    console.log("checking daily chat summary");
    const date = new Date();
    const guilds = client.guilds.cache;
    console.log("checking daily chat summary for", guilds.size, "guilds");
    for (let guild of guilds.values()) {
        const data = loadDailyChatSummary(guild.id);
        for (let a of data) {
            if (a.lastSentDay === date.getUTCDay() && a.lastSentMonth === date.getUTCMonth()) continue;

            const channel = guild.channels.cache.get(a.channelID);
            if (!channel) continue;
            if (!channel.isTextBased()) continue;

            const selfMember = getSelfMember(guild);
            if (!selfMember) continue;
            if (!selfMember.permissionsIn(channel).has("SendMessages")) continue;

            const embed = {
                title: `Chat Summary for ${date.getUTCMonth() + 1}/${date.getUTCDate() - 1}/${date.getUTCFullYear()}`,
                description:
                    `**Messages: ${a.messages}**\n` +
                    `"owo"s: ${a.special.owo}\n` +
                    `":3"s: ${a.special.catface}\n` +
                    `meows: ${a.special.meow}\n` +
                    `Users: ${a.users.length}\n\n` +
                    `Top 5 Users:\n` +
                    a.users
                        .sort((a, b) => b.messages - a.messages)
                        .slice(0, 5)
                        .map((v, i) => `${i + 1}. <@${v.userID}>: ${v.messages}`)
                        .join("\n"),
                color: 0x00ff00
            };
            await channel.send({ embeds: [embed] });

            a.messages = 0;
            a.special.owo = 0;
            a.special.catface = 0;
            a.special.meow = 0;
            a.users = [];
            a.lastSentDay = date.getUTCDay();
            a.lastSentMonth = date.getUTCMonth();

            saveDailyChatSummary(guild.id, data);
        }
    }
}

export class DailyChatSummary implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";

    async onEmojiCreate(emoji: Emoji): Promise<void> {}

    async onEmojiDelete(emoji: Emoji): Promise<void> {}

    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}

    async onStickerCreate(sticker: Sticker): Promise<void> {}

    async onStickerDelete(sticker: Sticker): Promise<void> {}

    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        await handleSettingsCommands(interaction);
    }

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}

    async onRoleCreate(role: Role): Promise<void> {}

    async onRoleEdit(before: Role, after: Role): Promise<void> {}

    async onRoleDelete(role: Role): Promise<void> {}

    async onChannelCreate(role: Channel): Promise<void> {}

    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}

    async onChannelDelete(role: Channel): Promise<void> {}

    async onMessage(msg: Message<boolean>): Promise<void> {
        await handleMessage(msg);
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
        await checkDailyChatSummary(client);
        setInterval(() => checkDailyChatSummary(client), 1000 * 60 * 60);
    }
}
