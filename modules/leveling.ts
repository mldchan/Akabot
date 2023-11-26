import { ChatInputCommandInteraction, CacheType, ButtonInteraction, Role, Channel, Message, GuildMember, SlashCommandBuilder, EmbedBuilder } from "discord.js";
import { AllCommands, Module } from "./type";
import { addPointsToUser, getUserLevel, getUserPoints, getUserRequirementForNextLevel } from "../data/leveling";

function getFormattedDate() {
    const date = new Date();
    return `${date.getUTCFullYear()}/${date.getUTCMonth()}/${date.getUTCDate()} ${date.getUTCHours()}:${date.getUTCMinutes()}:${date.getUTCSeconds()} UTC`;
}

export class LevelingModule implements Module {
    commands: AllCommands = [new SlashCommandBuilder().setName("level").setDescription("Get your current level").setDMPermission(false), new SlashCommandBuilder().setName("rank").setDescription("Get your current level").setDMPermission(false)];
    selfMemberId: string = "";
    async onSlashCommand(interaction: ChatInputCommandInteraction<CacheType>): Promise<void> {
        if (interaction.commandName !== "level" && interaction.commandName !== "rank") return;
        if (!interaction.guild) return;
        const points = getUserPoints(interaction.guild.id, interaction.user.id);
        const level = getUserLevel(points);
        const pointsToNext = getUserRequirementForNextLevel(points);
        const embed = new EmbedBuilder()
            .setTitle(`Level - ${interaction.user.displayName}`)
            .setDescription(`You are currently on level ${level} (${points} XP)\nYou need ${pointsToNext - points} XP for next level.`)
            .setFooter({
                text: getFormattedDate()
            });
        await interaction.reply({
            embeds: [embed]
        });
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
        addPointsToUser(msg.guild.id, msg.author.id, msg.content.length);
    }
    async onMessageDelete(msg: Message<boolean>): Promise<void> {}
    async onMessageEdit(before: Message<boolean>, after: Message<boolean>): Promise<void> {}
    async onMemberJoin(member: GuildMember): Promise<void> {}
    async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}
    async onMemberLeave(member: GuildMember): Promise<void> {}
}
