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
    Sticker, SlashCommandBuilder, Client
} from "discord.js";
import { AllCommands, Module } from "@/modules/type";
import * as fs from "fs";

type AnalyticsBlock = { [key: string]: number | undefined };
type AnalyticsDay = { [key: number]: AnalyticsBlock };
type AnalyticsMonth = { [key: number]: AnalyticsDay };
type AnalyticsYear = { [key: number]: AnalyticsMonth };

function readData(): AnalyticsYear {
    if (!fs.existsSync("./store")) fs.mkdirSync("./store");
    if (!fs.existsSync("./store/analytics.json")) fs.writeFileSync("./store/analytics.json", "{}");
    const data = JSON.parse(fs.readFileSync("./store/analytics.json", "utf-8")) as AnalyticsYear;
    const now = new Date();
    if (!data[now.getFullYear()]) data[now.getFullYear()] = {};
    if (!data[now.getFullYear()][now.getMonth()]) data[now.getFullYear()][now.getMonth()] = {};
    if (!data[now.getFullYear()][now.getMonth()][now.getDate()])
        data[now.getFullYear()][now.getMonth()][now.getDate()] = {};
    return data;
}

function writeData(x: AnalyticsYear) {
    fs.writeFileSync("./store/analytics.json", JSON.stringify(x));
}

export class AnalyticsModule implements Module {
    async onEmojiCreate(emoji: Emoji): Promise<void> {}
    async onEmojiDelete(emoji: Emoji): Promise<void> {}
    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {}
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    commands: AllCommands = [
        new SlashCommandBuilder()
            .setName("privacy")
            .setDescription("Privacy")
    ];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        let file = readData();
        const n = new Date();
        file[n.getFullYear()][n.getMonth()][n.getDate()][interaction.commandName] =
            (file[n.getFullYear()][n.getMonth()][n.getDate()][interaction.commandName] ?? 0) + 1;
        console.log(
            "analytics",
            interaction.commandName,
            n.getFullYear(),
            n.getMonth(),
            n.getDate(),
            file[n.getFullYear()][n.getMonth()][n.getDate()][interaction.commandName]
        );
        writeData(file);
    }
    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}
    async onRoleCreate(role: Role): Promise<void> {}
    async onRoleEdit(before: Role, after: Role): Promise<void> {}
    async onRoleDelete(role: Role): Promise<void> {}
    async onChannelCreate(role: Channel): Promise<void> {}
    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}
    async onChannelDelete(role: Channel): Promise<void> {}
    async onMessage(msg: Message<boolean>): Promise<void> {}
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
