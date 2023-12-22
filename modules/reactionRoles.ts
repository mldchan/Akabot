import {
    ActionRowBuilder,
    APIRole,
    ButtonBuilder,
    ButtonComponent,
    ButtonInteraction,
    ButtonStyle,
    CacheType,
    Channel,
    ChatInputCommandInteraction, Client,
    Emoji,
    Guild,
    GuildMember,
    Message,
    PermissionsBitField,
    Role,
    Sticker
} from "discord.js";
import { AllCommands, Module } from "./type";
import { getSelfMember } from "../utilities/useful";

async function createReactionRoleMessage(msg: string, roles: (Role | APIRole)[], interaction: ChatInputCommandInteraction<CacheType>, modeCode: string) {
    let rows: ActionRowBuilder<ButtonBuilder>[] = [];
    let currentRow = new ActionRowBuilder<ButtonBuilder>();
    for (const i of roles) {
        if (currentRow.components.length === 5) {
            rows.push(currentRow);
            currentRow = new ActionRowBuilder<ButtonBuilder>();
        }
        currentRow.addComponents(new ButtonBuilder().setCustomId(`rr${modeCode}-${i.id}`).setLabel(i.name).setStyle(ButtonStyle.Primary));
    }

    await interaction.channel!.send({
        content: msg,
        components: [...rows, currentRow]
    });
}

async function handleCreationOfReactionRoles(interaction: ChatInputCommandInteraction<CacheType>) {
    if (interaction.commandName !== "settings" || interaction.options.getSubcommandGroup(false) !== "reactionroles" || interaction.options.getSubcommand(false) !== "new") return;
    if (!interaction.channel) return;
    if (!interaction.member) return;
    if (!interaction.guild) return;
    const member = interaction.guild.members.cache.get(interaction.user.id);
    if (!member) return;
    if (!member.permissions.has(PermissionsBitField.Flags.ManageRoles) && !member.permissions.has(PermissionsBitField.Flags.Administrator)) {
        await interaction.reply({
            content: "You do not have permission to create reaction roles",
            ephemeral: true
        });
    }

    const msg = interaction.options.getString("message")!;
    const mode = interaction.options.getString("mode")!;
    let roles = [interaction.options.getRole("role")!];
    const role2 = interaction.options.getRole("role-2");
    if (role2 !== null) roles.push(role2);
    const role3 = interaction.options.getRole("role-3");
    if (role3 !== null) roles.push(role3);
    const role4 = interaction.options.getRole("role-4");
    if (role4 !== null) roles.push(role4);
    const role5 = interaction.options.getRole("role-5");
    if (role5 !== null) roles.push(role5);
    const role6 = interaction.options.getRole("role-6");
    if (role6 !== null) roles.push(role6);
    const role7 = interaction.options.getRole("role-7");
    if (role7 !== null) roles.push(role7);
    const role8 = interaction.options.getRole("role-8");
    if (role8 !== null) roles.push(role8);
    const role9 = interaction.options.getRole("role-9");
    if (role9 !== null) roles.push(role9);

    switch (mode) {
        case "normal":
            await createReactionRoleMessage(msg, roles, interaction, "n");
            break;
        case "add":
            await createReactionRoleMessage(msg, roles, interaction, "a");
            break;
        case "remove":
            await createReactionRoleMessage(msg, roles, interaction, "r");
            break;
        case "single":
            await createReactionRoleMessage(msg, roles, interaction, "s");
            break;
    }

    await interaction.reply({
        content: "Created reaction role message",
        ephemeral: true
    });
}

async function handleNormalReactionRole(interaction: ButtonInteraction<CacheType>) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.message) return;
    if (!interaction.user) return;

    const selfMember = getSelfMember(interaction.guild);
    if (!selfMember) return;
    if (!selfMember.permissions.has("ManageRoles")) return;

    const member = interaction.member as GuildMember;

    const role = interaction.guild.roles.cache.get(interaction.customId.split("-")[1]);
    if (!role) return;

    if (selfMember.roles.highest.comparePositionTo(role) <= 0) {
        await interaction.reply({
            content: `I cannot give you the role **${role.name}** because I don't have permissions`,
            ephemeral: true
        });
        return;
    }

    if (member.roles.cache.has(role.id)) {
        await member.roles.remove(role);
        await interaction.reply({
            content: `Removed role **${role.name}** from you`,
            ephemeral: true
        });
    } else {
        await member.roles.add(role);
        await interaction.reply({
            content: `Added role **${role.name}** to you`,
            ephemeral: true
        });
    }
}

async function handleAddReactionRole(interaction: ButtonInteraction<CacheType>) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.message) return;
    if (!interaction.user) return;

    const selfMember = getSelfMember(interaction.guild);
    if (!selfMember) return;
    if (!selfMember.permissions.has("ManageRoles")) return;

    const member = interaction.member as GuildMember;

    const role = interaction.guild.roles.cache.get(interaction.customId.split("-")[1]);
    if (!role) return;
    if (selfMember.roles.highest.comparePositionTo(role) <= 0) {
        await interaction.reply({
            content: `I cannot give you the role **${role.name}** because I don't have permissions`,
            ephemeral: true
        });
        return;
    }

    if (member.roles.cache.has(role.id)) {
        await interaction.reply({
            content: `You already have role **${role.name}**`,
            ephemeral: true
        });
    } else {
        await member.roles.add(role);
        await interaction.reply({
            content: `Added role **${role.name}** to you`,
            ephemeral: true
        });
    }
}

async function handleRemoveReactionRole(interaction: ButtonInteraction<CacheType>) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.message) return;
    if (!interaction.user) return;
    const msg = interaction.message;
    const member = interaction.member as GuildMember;
    await member.fetch(true);
    const role = interaction.guild.roles.cache.get(interaction.customId.split("-")[1]);
    if (!role) return;
    if (msg.author.id !== interaction.client.user.id) return;
    if (member.roles.cache.has(role.id)) {
        try {
            await member.roles.remove(role);
        } catch (_) {
            await interaction.reply({
                content: `Failed to remove role **${role.name}** from you, contact the server administrators`,
                ephemeral: true
            });
            return;
        }
        await interaction.reply({
            content: `Removed role **${role.name}** from you`,
            ephemeral: true
        });
        return;
    }
    await interaction.reply({
        content: `You do not have role **${role.name}**`,
        ephemeral: true
    });
}

async function handleSingleReactionRole(interaction: ButtonInteraction<CacheType>) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (!interaction.message) return;
    if (!interaction.user) return;

    const msg = interaction.message;

    const selfMember = getSelfMember(interaction.guild);
    if (!selfMember) return;
    if (!selfMember.permissions.has("ManageRoles")) return;

    const member = interaction.member as GuildMember;

    const role = interaction.guild.roles.cache.get(interaction.customId.split("-")[1]);
    if (!role) return;
    if (selfMember.roles.highest.comparePositionTo(role) <= 0) {
        await interaction.reply({
            content: `I cannot give you the role **${role.name}** because I don't have permissions`,
            ephemeral: true
        });
        return;
    }

    if (member.roles.cache.has(role.id)) {
        await interaction.reply({
            content: `You already have role **${role.name}**`,
            ephemeral: true
        });
        return;
    }
    await member.roles.add(role);
    let components: ButtonComponent[] = [];
    msg.components.forEach((x) => components.push(...(x.components as ButtonComponent[])));

    const otherRoles = components
        .filter((i) => i.customId?.startsWith("rrs-") ?? false)
        .map((i) => i.customId?.split("-")[1] ?? "")
        .filter((i) => i !== role.id)
        .filter((i) => i !== "")
        .filter((i) => member.roles.cache.has(i))
        .filter((i) => selfMember.roles.highest.comparePositionTo(interaction.guild!.roles.cache.get(i)!) <= 0);

    if (otherRoles.length > 0) {
        await member.roles.remove(otherRoles);
    }
    const roleNames = otherRoles
        .map((i) => `**${interaction.guild!.roles.cache.get(i)?.name ?? ""}**`)
        .filter((x) => x !== "****")
        .join(", ");
    await interaction.reply({
        content: `Selected role **${role.name}** to you and removed: ${roleNames}`,
        ephemeral: true
    });
}

async function handleReactionRole(interaction: ButtonInteraction<CacheType>) {
    if (!interaction.guild) return;
    if (!interaction.member) return;
    if (interaction.user.id === interaction.client.user.id) return;
    if (interaction.customId.startsWith("rrn-")) {
        await handleNormalReactionRole(interaction);
    }
    if (interaction.customId.startsWith("rra-")) {
        await handleAddReactionRole(interaction);
    }
    if (interaction.customId.startsWith("rrr-")) {
        await handleRemoveReactionRole(interaction);
    }
    if (interaction.customId.startsWith("rrs-")) {
        await handleSingleReactionRole(interaction);
    }
}

export class ReactionRolesModule implements Module {
    commands: AllCommands = [];
    selfMemberId: string = "";

    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        await handleCreationOfReactionRoles(interaction);
    }

    async onButtonClick(interaction: ButtonInteraction<CacheType>): Promise<void> {
        await handleReactionRole(interaction);
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
    async onReady(client: Client): Promise<void> {}
}
