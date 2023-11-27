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

export class SettingsModule implements Module {
    commands: AllCommands = [
        new SettingsCommandBuilder()
            .addSettingsGroup(new SettingsGroupBuilder("logging").addChannelSetting(new ChannelSetting("channel", "loggingChannel")))
            .addSettingsGroup(new SettingsGroupBuilder("welcome").addChannelSetting(new ChannelSetting("channel", "welcomeChannel")))
            .addSettingsGroup(new SettingsGroupBuilder("goodbye").addChannelSetting(new ChannelSetting("channel", "goodbyeChannel")))
            .addSettingsGroup(new SettingsGroupBuilder("leveling").addChannelSetting(new ChannelSetting("channel", "levelingChannel")))
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
                    .addStringSetting(
                        new StringChoiceSetting(
                            "newmembers",
                            "AntiRaidNewMembers",
                            "How old does a member have to be to be on this server",
                            [
                                { display: "Disable auto-kick", value: "0" },
                                { display: "Auto-kick members younger than 1 day", value: "1" },
                                { display: "Auto-kick members younger than 3 days", value: "3" },
                                { display: "Auto-kick members younger than 7 days", value: "7" },
                                { display: "Auto-kick members younger than 14 days", value: "14" },
                                { display: "Auto-kick members younger than 30 days", value: "30" }
                            ]
                        )
                    )
                    .addToggleSetting(new ToggleSetting("nopfp", "AntiRaidNoPFP", "Kick members with no profile picture"))
                    .addToggleSetting(new ToggleSetting("spamdelete", "AntiRaidSpamDelete", "Delete messages from spammers"))
                    .addToggleSetting(new ToggleSetting("spamtimeout", "AntiRaidSpamTimeout", "Timeout spammers for a short period"))
                    .addToggleSetting(new ToggleSetting("spamalert", "AntiRaidSpamSendAlert", "Tell the spammer to stop spamming"))
            )
    ];
    settingsMaps = [];
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

        const subcommandGroup = interaction.options.getSubcommandGroup();
        if (!subcommandGroup) return;
        const subcommand = interaction.options.getSubcommand(false);
        if (!subcommand) return;
        const commandBuilder = this.commands[0] as SettingsCommandBuilder;
        const settingsKey = commandBuilder.findSettingsKeyForCommand(subcommandGroup, subcommand);
        if (!settingsKey) return;
        const settingType = commandBuilder.findSettingTypeForCommand(subcommandGroup, subcommand);
        if (!settingType) return;
        const settingDesc = commandBuilder.findDescriptionForCommand(subcommandGroup, subcommand);
        if (!settingDesc) return;

        switch (settingType) {
            case "channel": {
                const newValue = interaction.options.getChannel("newvalue");
                if (newValue === null || newValue === undefined) {
                    const current = getSetting(interaction.guild.id, settingsKey, "");
                    const currentChannel = interaction.guild.channels.cache.get(current);
                    await interaction.reply({
                        content: `\`${settingDesc}\` is currently set to \`${currentChannel?.name ?? current}\``,
                        ephemeral: true
                    });
                    break;
                }
                setChannel(subcommandGroup, settingsKey, interaction, this.selfMemberId);
                break;
            }
            case "string": {
                const value = interaction.options.getString("newvalue");
                if (value === null || value === undefined) {
                    await interaction.reply({
                        content: `\`${settingDesc}\` is currently set to \`${getSetting(interaction.guild.id, settingsKey, "")}\``,
                        ephemeral: true
                    });
                    break;
                }
                setSetting(interaction.guild.id, settingsKey, value);
                await interaction.reply({
                    content: `Set \`${settingDesc}\` to \`${value}\``,
                    ephemeral: true
                });
                break;
            }
            case "toggle": {
                const value = interaction.options.getBoolean("newvalue");
                if (value === null || value === undefined) {
                    const current = getSetting(interaction.guild.id, settingsKey, "no");
                    await interaction.reply({
                        content: `\`${settingDesc}\` is currently set to \`${current}\``,
                        ephemeral: true
                    });
                    break;
                }
                setSetting(interaction.guild.id, settingsKey, value ? "yes" : "no");
                await interaction.reply({
                    content: `Set \`${settingDesc}\` to \`${value ? "yes" : "no"}\``,
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
