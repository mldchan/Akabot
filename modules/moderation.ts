import {
    ButtonInteraction,
    CacheType,
    Channel,
    ChatInputCommandInteraction,
    Emoji,
    Guild,
    GuildMember,
    Message,
    PermissionFlagsBits,
    Role,
    SlashCommandBuilder,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import { getSelfMember } from "../utilities/useful";

export class ModerationModule implements Module {
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
    async onTick(): Promise<void> {}
}

async function attemptToSendDM(member: GuildMember, type: "banned" | "muted" | "kicked", reason: string | undefined) {
    if (reason === undefined) reason = "N/A";
    try {
        await member.send(`You have been ${type} for ${reason}`);
    } catch (_) {
    }
}

async function handleBanMember(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;

    const selfMember = getSelfMember(interaction.guild);
    if (!selfMember) return;

    if (!selfMember.permissions.has(PermissionFlagsBits.BanMembers) && !selfMember.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "I do not have the permission to ban members",
            ephemeral: true
        });
        return;
    }

    const moderator = interaction.guild.members.cache.find((x) => x.user.id === interaction.user.id);
    if (!moderator) return;

    const targetUser = interaction.options.getUser("user", true);
    const targetMember = interaction.guild.members.cache.find((x) => x.user.id === targetUser.id);
    if (!targetMember) return;

    if (targetUser.id === moderator.id) {
        await interaction.reply({
            content: "You cannot ban yourself",
            ephemeral: true
        });
        return;
    }

    if (selfMember.roles.highest.comparePositionTo(targetMember.roles.highest) <= 0) {
        await interaction.reply({
            content: "I do not have permissions to ban this user",
            ephemeral: true
        });
    }

    if (moderator.roles.highest.comparePositionTo(targetMember.roles.highest) <= 0) {
        await interaction.reply({
            content: "I do not have permissions to ban this user",
            ephemeral: true
        });
    }

    if (!moderator.permissions.has(PermissionFlagsBits.BanMembers) && !moderator.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "You do not have the permission to ban members",
            ephemeral: true
        });
        return;
    }

    const reason = interaction.options.getString("reason", false);
    await attemptToSendDM(targetMember, "banned", reason ?? undefined);

    await interaction.guild.members.ban(targetUser, { reason: reason ?? undefined });

    await interaction.reply({
        content: `Banned ${targetUser.username}`,
        ephemeral: true
    });
}

async function handleKickMember(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;

    const selfMember = getSelfMember(interaction.guild);
    if (!selfMember) return;

    if (!selfMember.permissions.has(PermissionFlagsBits.KickMembers) && !selfMember.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "I do not have the permission to kick members",
            ephemeral: true
        });
        return;
    }

    const moderator = interaction.guild.members.cache.find((x) => x.user.id === interaction.user.id);
    if (!moderator) return;

    const targetUser = interaction.options.getUser("user", true);
    const targetMember = interaction.guild.members.cache.find((x) => x.user.id === targetUser.id);
    if (!targetMember) return;

    if (moderator.id === targetMember.id) {
        await interaction.reply({
            content: "You cannot kick yourself",
            ephemeral: true
        });
        return;
    }

    if (selfMember.roles.highest.comparePositionTo(targetMember.roles.highest) <= 0) {
        await interaction.reply({
            content: "I do not have permissions to kick this user",
            ephemeral: true
        });
        return;
    }
    if (moderator.roles.highest.comparePositionTo(targetMember.roles.highest) <= 0) {
        await interaction.reply({
            content: "I do not have permissions to kick this user",
            ephemeral: true
        });
        return;
    }

    if (!moderator.permissions.has(PermissionFlagsBits.KickMembers) && !moderator.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "You do not have the permission to kick members",
            ephemeral: true
        });
        return;
    }

    const user = interaction.options.getUser("user", true);
    const reason = interaction.options.getString("reason", false);
    await attemptToSendDM(targetMember, "kicked", reason ?? undefined);

    await interaction.guild.members.kick(user, reason ?? undefined);

    await interaction.reply({
        content: `Kicked ${user.username}`,
        ephemeral: true
    });
}

async function handleMuteMember(interaction: ChatInputCommandInteraction<CacheType>) {
    if (!interaction.guild) return;

    const selfMember = getSelfMember(interaction.guild);
    if (!selfMember) return;

    if (!selfMember.permissions.has(PermissionFlagsBits.MuteMembers) && !selfMember.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "I do not have the permission to mute members",
            ephemeral: true
        });
        return;
    }


    const moderator = interaction.guild.members.cache.find((x) => x.user.id === interaction.user.id);
    if (!moderator) return;

    const targetUser = interaction.options.getUser("user", true);
    const targetMember = interaction.guild.members.cache.find((x) => x.user.id === targetUser.id);
    if (!targetMember) return;

    if (moderator.id === targetMember.id) {
        await interaction.reply({
            content: "You cannot mute yourself",
            ephemeral: true
        });
        return;
    }

    if (selfMember.roles.highest.comparePositionTo(targetMember.roles.highest) <= 0) {
        await interaction.reply({
            content: "I do not have permissions to mute this user",
            ephemeral: true
        });
        return;
    }

    if (moderator.roles.highest.comparePositionTo(targetMember.roles.highest) <= 0) {
        await interaction.reply({
            content: "I do not have permissions to mute this user",
            ephemeral: true
        });
        return;
    }

    if (!moderator.permissions.has(PermissionFlagsBits.ManageRoles) && !moderator.permissions.has(PermissionFlagsBits.Administrator)) {
        await interaction.reply({
            content: "You do not have the permission to mute members",
            ephemeral: true
        });
        return;
    }
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
        return;
    }

    await attemptToSendDM(targetMember, "muted", reason ?? undefined);
    await targetMember.timeout(time * 1000, reason ?? undefined);

    await interaction.reply({
        content: `Muted ${user.username} for ${time} minutes`,
        ephemeral: true
    });
}
