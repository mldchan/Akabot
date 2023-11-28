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
    Sticker,
    SlashCommandBuilder,
    PermissionFlagsBits
} from "discord.js";
import { AllCommands, Module } from "./type";

export class ModerationModule implements Module {
    async onEmojiCreate(emoji: Emoji): Promise<void> {}
    async onEmojiDelete(emoji: Emoji): Promise<void> {}
    async onEmojiEdit(before: Emoji, after: Emoji): Promise<void> {}
    async onStickerCreate(sticker: Sticker): Promise<void> {}
    async onStickerDelete(sticker: Sticker): Promise<void> {}
    async onStickerEdit(before: Sticker, after: Sticker): Promise<void> {}
    commands: AllCommands = [
        new SlashCommandBuilder()
            .setName("ban")
            .setDescription("Ban a user")
            .setDefaultMemberPermissions(PermissionFlagsBits.BanMembers)
            .setDMPermission(false)
            .addUserOption((option) => option.setName("user").setDescription("The user to ban").setRequired(true))
            .addStringOption((option) => option.setName("reason").setDescription("The reason for the ban").setRequired(false)),
        new SlashCommandBuilder()
            .setName("kick")
            .setDescription("Kick a user")
            .setDefaultMemberPermissions(PermissionFlagsBits.KickMembers)
            .setDMPermission(false)
            .addUserOption((option) => option.setName("user").setDescription("The user to kick").setRequired(true))
            .addStringOption((option) => option.setName("reason").setDescription("The reason for the kick").setRequired(false)),
        new SlashCommandBuilder()
            .setName("mute")
            .setDescription("Mute a user")
            .setDefaultMemberPermissions(PermissionFlagsBits.ManageRoles)
            .setDMPermission(false)
            .addUserOption((option) => option.setName("user").setDescription("The user to mute").setRequired(true))
            .addNumberOption((option) =>
                option.setName("hours").setDescription("The duration of the mute in hours (will add up)").setRequired(true)
            )
            .addStringOption((option) => option.setName("reason").setDescription("The reason for the mute").setRequired(false))
            .addNumberOption((option) =>
                option.setName("days").setDescription("The duration of the mute in days (will add up)").setRequired(false)
            )
    ];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (!interaction.guild) return;
        switch (interaction.commandName) {
            case "ban": {
                await handleBanMember(interaction);
                break;
            }
            case "kick": {
                await handleKickMember(interaction);
                break;
            }
            case "mute": {
                await handleMuteMember(interaction);
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
}

async function attemptToSendDM(member: GuildMember, type: "banned" | "muted" | "kicked", reason: string | undefined) {
    if (reason === undefined) reason = "N/A";
    try {
        await member.send(`You have been ${type} for ${reason}`);
    } catch (_) {}
}

async function handleBanMember(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;
    const selfMember = interaction.guild.members.cache.get(interaction.client.user.id);
    if (!selfMember) return;
    if (selfMember.permissions.has(PermissionFlagsBits.BanMembers) || selfMember.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "I do not have the permission to ban members",
            ephemeral: true
        });
        return;
    }
    const member = interaction.guild.members.cache.find((x) => x.user.id === interaction.user.id);
    if (!member) return;
    if (!member.permissions.has(PermissionFlagsBits.BanMembers) && !member.permissions.has(PermissionFlagsBits.Administrator)) return;
    const user = interaction.options.getUser("user", true);
    const reason = interaction.options.getString("reason", false);
    await attemptToSendDM(member, "banned", reason ?? undefined);
    try {
        await interaction.guild.members.ban(user, { reason: reason ?? undefined });
    } catch (_) {
        await interaction.reply({
            content: `Could not ban ${user.username}, check the bot permissions`,
            ephemeral: true
        });
        return;
    }

    await interaction.reply({
        content: `Banned ${user.username}`,
        ephemeral: true
    });
}

async function handleKickMember(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;
    const selfMember = interaction.guild.members.cache.get(interaction.client.user.id);
    if (!selfMember) return;
    if (selfMember.permissions.has(PermissionFlagsBits.KickMembers) || selfMember.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "I do not have the permission to kick members",
            ephemeral: true
        });
        return;
    }
    const member = interaction.guild.members.cache.find((x) => x.user.id === interaction.user.id);
    if (!member) return;
    if (!member.permissions.has(PermissionFlagsBits.KickMembers) && !member.permissions.has(PermissionFlagsBits.Administrator)) return;
    const user = interaction.options.getUser("user", true);
    const reason = interaction.options.getString("reason", false);
    await attemptToSendDM(member, "kicked", reason ?? undefined);
    try {
        await interaction.guild.members.kick(user, reason ?? undefined);
    } catch (_) {
        await interaction.reply({
            content: `Could not kick ${user.username}, check the bot permissions`,
            ephemeral: true
        });
        return;
    }

    await interaction.reply({
        content: `Kicked ${user.username}`,
        ephemeral: true
    });
}

async function handleMuteMember(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;
    const selfMember = interaction.guild.members.cache.get(interaction.client.user.id);
    if (!selfMember) return;
    if (selfMember.permissions.has(PermissionFlagsBits.MuteMembers) || selfMember.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "I do not have the permission to mute members",
            ephemeral: true
        });
        return;
    }

    const member = interaction.guild.members.cache.find((x) => x.user.id === interaction.user.id);
    if (!member) return;
    if (!member.permissions.has(PermissionFlagsBits.ManageRoles) && !member.permissions.has(PermissionFlagsBits.Administrator)) return;
    const user = interaction.options.getUser("user", true);
    const reason = interaction.options.getString("reason", false);
    const hours = interaction.options.getNumber("hours", true);
    const days = interaction.options.getNumber("days", false);

    const time = hours * 60 + (days ?? 0) * 24 * 60;
    if (time > 604800) {
        await interaction.reply({
            content: "You can only mute for up to 7 days",
            ephemeral: true
        });
    }
    const target = interaction.guild.members.cache.find((x) => x.user.id === user.id);
    if (!target) return;
    await attemptToSendDM(member, "muted", reason ?? undefined);
    try {
        await target.timeout(time * 1000, reason ?? undefined);
    } catch (_) {
        await interaction.reply({
            content: "Could not mute the user",
            ephemeral: true
        });
        return;
    }

    await interaction.reply({
        content: `Muted ${user.username} for ${time} minutes`,
        ephemeral: true
    });
}
