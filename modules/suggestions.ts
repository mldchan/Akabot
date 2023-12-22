import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction, Client,
    Emoji,
    Guild,
    GuildMember,
    Message,
    Role,
    SlashCommandBuilder,
    SlashCommandSubcommandsOnlyBuilder,
    Sticker
} from "discord.js";
import { Module } from "./type";
import { addBugReport, addSuggestion } from "../data/feedback";

export class Suggestions implements Module {
    async onRoleEdit(before: Role, after: Role): Promise<void> {}
    async onChannelCreate(role: Channel): Promise<void> {}
    async onChannelEdit(before: Channel, after: Channel): Promise<void> {}
    async onChannelDelete(role: Channel): Promise<void> {}
    async onMessageDelete(msg: Message<boolean>): Promise<void> {}
    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {}
    async onMemberJoin(member: GuildMember): Promise<void> {}
    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}
    async onMemberLeave(member: GuildMember): Promise<void> {}
    commands: SlashCommandBuilder[] | SlashCommandSubcommandsOnlyBuilder[] = [
        new SlashCommandBuilder()
            .setName("feedback")
            .setDescription("Send feedback to the Discord bot owner")
            .addSubcommand((subcommand) =>
                subcommand
                    .setName("suggest")
                    .setDescription("Suggest a feature to be added to the bot")
                    .addStringOption((option) =>
                        option.setName("suggestion").setDescription("The suggestion you want to send").setRequired(true)
                    )
            )
            .addSubcommand((subcommand) =>
                subcommand
                    .setName("bug")
                    .setDescription("Create a bug report")
                    .addStringOption((option) => option.setName("bug").setDescription("The bug you want to report").setRequired(true))
            )
    ];
    selfMemberId: string = "";
    async onMessage(msg: Message): Promise<void> {}
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (interaction.commandName !== "feedback") return;
        switch (interaction.options.getSubcommand(true)) {
            case "suggest": {
                const a = interaction.options.getString("suggestion", true);
                addSuggestion(interaction.user.username, a);
                await interaction.reply({
                    content: "Your suggestion has been sent!",
                    ephemeral: true
                });
                break;
            }
            case "bug": {
                const b = interaction.options.getString("bug", true);
                addBugReport(interaction.user.username, b);
                await interaction.reply({
                    content: "Your bug report has been sent!",
                    ephemeral: true
                });
                break;
            }
        }
    }
    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {}

    async onRoleCreate(role: Role): Promise<void> {}
    async onRoleDelete(role: Role): Promise<void> {}
    async onGuildAdd(guild: Guild): Promise<void> {}
    async onGuildRemove(guild: Guild): Promise<void> {}
    async onGuildEdit(before: Guild, after: Guild): Promise<void> {}
    async onEmojiCreate(emoji: Emoji): Promise<void> {}
    async onEmojiDelete(emoji: Emoji): Promise<void> {}
    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {}
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    async onReady(client: Client): Promise<void> {}
}
