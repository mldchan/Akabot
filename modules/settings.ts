import {
    ChatInputCommandInteraction,
    CacheType,
    ButtonInteraction,
    Role,
    Channel,
    Message,
    GuildMember,
    PermissionsBitField,
    SlashCommandSubcommandBuilder,
    Guild,
    Emoji,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import {
    ChannelSetting,
    SettingsCommandBuilder,
    SettingsGroupBuilder,
    StringChoiceSetting,
    ToggleSetting,
    setChannel
} from "../types/settings";
import { getSetting, setSetting } from "../data/settings";

async function handleLoggingSubcommands(interaction: ChatInputCommandInteraction<CacheType>, selfMemberId: string) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.options) return;
    const loggingGroup = interaction.options.getSubcommand();
    if (loggingGroup === "channel") {
        setChannel("logging", "loggingChannel", interaction, selfMemberId);
    }
}

async function handleWelcomeSubcommands(interaction: ChatInputCommandInteraction<CacheType>, selfMemberId: string) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.options) return;
    const group = interaction.options.getSubcommand();
    if (group === "channel") {
        setChannel("welcome", "welcomeChannel", interaction, selfMemberId);
    }
}
async function handleGoodbyeSubcommands(interaction: ChatInputCommandInteraction<CacheType>, selfMemberId: string) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.options) return;
    const group = interaction.options.getSubcommand();
    if (group === "channel") {
        setChannel("goodbye", "goodbyeChannel", interaction, selfMemberId);
    }
}

async function handleLevelingSubcommands(interaction: ChatInputCommandInteraction<CacheType>, selfMemberId: string) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.options) return;
    const group = interaction.options.getSubcommand();
    if (group === "channel") {
        setChannel("leveling", "levelingChannel", interaction, selfMemberId);
    }
}

async function handleAntiRaidSubcommands(interaction: ChatInputCommandInteraction<CacheType>, selfMemberId: string) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.options) return;
    const group = interaction.options.getSubcommand();
    if (group === "newmembers") {
        const value = interaction.options.getString("value", true);
        setSetting(interaction.guild.id, "AntiRaidNewMembers", value);
        if (value === "0") {
            await interaction.reply({
                content: "Disabled anti-raid",
                ephemeral: true
            });
            return;
        }
        await interaction.reply({
            content: `Set anti-raid to ${value} days`,
            ephemeral: true
        });
    }
    if (group === "nopfp") {
        const value = interaction.options.getBoolean("value", true);
        setSetting(interaction.guild.id, "AntiRaidKickNoPFP", value ? "yes" : "no");
        await interaction.reply({
            content: `Set \`kick members without a profile picture\` to \`${value ? "yes" : "no"}\``,
            ephemeral: true
        });
    }
    if (group === "spamdetection") {
        const value = interaction.options.getBoolean("spamdetection");
        if (value === null || value === undefined) {
            const current = getSetting(interaction.guild.id, "AntiRaidSpamDetection", "no");
            await interaction.reply({
                content: `\`spam detection\` is currently set to \`${current}\``,
                ephemeral: true
            });
            return;
        }
        setSetting(interaction.guild.id, "AntiRaidSpamDetection", value ? "yes" : "no");
        await interaction.reply({
            content: `Set \`spam detection\` to \`${value ? "yes" : "no"}\``,
            ephemeral: true
        });
    }
    if (group === "spamdelete") {
        const value = interaction.options.getBoolean("spamdelete");
        if (value === null || value === undefined) {
            const current = getSetting(interaction.guild.id, "AntiRaidSpamDelete", "no");
            await interaction.reply({
                content: `\`delete spam messages\` is currently set to \`${current}\``,
                ephemeral: true
            });
            return;
        }
        setSetting(interaction.guild.id, "AntiRaidSpamDelete", value ? "yes" : "no");
        await interaction.reply({
            content: `Set \`delete spam messages\` to \`${value ? "yes" : "no"}\``,
            ephemeral: true
        });
    }
    if (group === "spamtimeout") {
        const value = interaction.options.getBoolean("spamtimeout");
        if (value === null || value === undefined) {
            const current = getSetting(interaction.guild.id, "AntiRaidSpamTimeout", "no");
            await interaction.reply({
                content: `\`timeout spammers\` is currently set to \`${current}\``,
                ephemeral: true
            });
            return;
        }
        setSetting(interaction.guild.id, "AntiRaidSpamTimeout", value ? "yes" : "no");
        await interaction.reply({
            content: `Set \`timeout spammers\` to \`${value ? "yes" : "no"}\``,
            ephemeral: true
        });
    }
    if (group === "spamalert") {
        const value = interaction.options.getBoolean("spamalert");
        if (value === null || value === undefined) {
            const current = getSetting(interaction.guild.id, "AntiRaidSpamSendAlert", "no");
            await interaction.reply({
                content: `\`tell spammers to stop spamming\` is currently set to \`${current}\``,
                ephemeral: true
            });
            return;
        }
        setSetting(interaction.guild.id, "AntiRaidSpamSendAlert", value ? "yes" : "no");
        await interaction.reply({
            content: `Set \`tell spammers to stop spamming\` to \`${value ? "yes" : "no"}\``,
            ephemeral: true
        });
    }
}

export class SettingsModule implements Module {
    commands: AllCommands = [
        new SettingsCommandBuilder()
            .addSettingsGroup(new SettingsGroupBuilder("logging").addChannelSetting(new ChannelSetting("channel")))
            .addSettingsGroup(new SettingsGroupBuilder("welcome").addChannelSetting(new ChannelSetting("channel")))
            .addSettingsGroup(new SettingsGroupBuilder("goodbye").addChannelSetting(new ChannelSetting("channel")))
            .addSettingsGroup(new SettingsGroupBuilder("leveling").addChannelSetting(new ChannelSetting("channel")))
            .addSettingsGroup(
                new SettingsGroupBuilder("reactionroles").addSubcommand(
                    new SlashCommandSubcommandBuilder()
                        .setName("new")
                        .setDescription("Create a reaction role")
                        .addStringOption((msg) => msg.setName("message").setDescription("The message").setRequired(true))
                        .addStringOption((mode) =>
                            mode
                                .setName("mode")
                                .setDescription("Mode to use this in")
                                .setChoices(
                                    {
                                        name: "Normal - Allow adding and removing",
                                        value: "normal"
                                    },
                                    { name: "Add only", value: "add" },
                                    { name: "Remove only", value: "remove" },
                                    {
                                        name: "Only allow a single role",
                                        value: "single"
                                    }
                                )
                                .setRequired(true)
                        )
                        .addRoleOption((role) => role.setName("role").setDescription("The role").setRequired(true))
                        .addRoleOption((role) => role.setName("role-2").setDescription("The role"))
                        .addRoleOption((role) => role.setName("role-3").setDescription("The role"))
                        .addRoleOption((role) => role.setName("role-4").setDescription("The role"))
                        .addRoleOption((role) => role.setName("role-5").setDescription("The role"))
                        .addRoleOption((role) => role.setName("role-6").setDescription("The role"))
                        .addRoleOption((role) => role.setName("role-7").setDescription("The role"))
                        .addRoleOption((role) => role.setName("role-8").setDescription("The role"))
                        .addRoleOption((role) => role.setName("role-9").setDescription("The role"))
                )
            )
            .addSettingsGroup(
                new SettingsGroupBuilder("antiraid")
                    .addStringChoiceSetting(
                        new StringChoiceSetting("newmembers", [
                            { display: "Disable auto-kick", value: "0" },
                            { display: "Auto-kick members younger than 1 day", value: "1" },
                            { display: "Auto-kick members younger than 3 days", value: "3" },
                            { display: "Auto-kick members younger than 7 days", value: "7" },
                            { display: "Auto-kick members younger than 14 days", value: "14" },
                            { display: "Auto-kick members younger than 30 days", value: "30" }
                        ])
                    )
                    .addToggleSetting(new ToggleSetting("nopfp", "Kick members with no profile picture."))
                    .addToggleSetting(new ToggleSetting("spamdetection", "Kick members that spam."))
                    .addToggleSetting(new ToggleSetting("spamdelete", "Delete messages from spammers."))
                    .addToggleSetting(new ToggleSetting("spamtimeout", "Timeout spammers for a short period."))
                    .addToggleSetting(new ToggleSetting("spamalert", "Tell the spammer to stop spamming."))
            )
    ];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (interaction.commandName !== "settings") return;
        if (!interaction.guild) return;
        if (!interaction.member) return;
        if (!interaction.options) return;
        const member = interaction.member as GuildMember;
        if (
            !member.permissions.has(PermissionsBitField.Flags.ManageGuild) &&
            !member.permissions.has(PermissionsBitField.Flags.Administrator)
        ) {
            await interaction.reply({
                content: "You do not have permissions",
                ephemeral: true
            });
            return;
        }

        const subcommand = interaction.options.getSubcommandGroup();
        if (subcommand === "logging") {
            await handleLoggingSubcommands(interaction, this.selfMemberId);
        }
        if (subcommand === "welcome") {
            await handleWelcomeSubcommands(interaction, this.selfMemberId);
        }
        if (subcommand === "goodbye") {
            await handleGoodbyeSubcommands(interaction, this.selfMemberId);
        }
        if (subcommand === "leveling") {
            await handleLevelingSubcommands(interaction, this.selfMemberId);
        }
        if (subcommand === "antiraid") {
            await handleAntiRaidSubcommands(interaction, this.selfMemberId);
        }
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
    async onEmojiCreate(emoji: Emoji): Promise<void> {}
    async onEmojiDelete(emoji: Emoji): Promise<void> {}
    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {}
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
}
