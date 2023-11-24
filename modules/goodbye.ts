import {
  ChatInputCommandInteraction,
  CacheType,
  ButtonInteraction,
  Role,
  Channel,
  Message,
  GuildMember,
  EmbedBuilder,
} from "discord.js";
import { AllCommands, Module } from "./type";
import { getSetting } from "../data/settings";

export class GoodbyeModule implements Module {
  commands: AllCommands = [];
  selfMemberId: string = "";
  async onSlashCommand(
    interaction: ChatInputCommandInteraction<CacheType>
  ): Promise<void> {}
  async onButtonClick(
    interaction: ButtonInteraction<CacheType>
  ): Promise<void> {}
  async onRoleCreate(role: Role): Promise<void> {}
  async onRoleEdit(before: Role, after: Role): Promise<void> {}
  async onRoleDelete(role: Role): Promise<void> {}
  async onChannelCreate(role: Channel): Promise<void> {}
  async onChannelEdit(before: Channel, after: Channel): Promise<void> {}
  async onChannelDelete(role: Channel): Promise<void> {}
  async onMessage(msg: Message<boolean>): Promise<void> {}
  async onMessageDelete(msg: Message<boolean>): Promise<void> {}
  async onMessageEdit(
    before: Message<boolean>,
    after: Message<boolean>
  ): Promise<void> {}
  async onMemberJoin(member: GuildMember): Promise<void> {}
  async onMemberEdit(before: GuildMember, after: GuildMember): Promise<void> {}
  async onMemberLeave(member: GuildMember): Promise<void> {
    const channel = getSetting(member.guild.id, "goodbyeChannel", "");
    if (channel === "") return;
    const channelRes = member.guild.channels.cache.get(channel);
    if (!channelRes) return;
    if (!channelRes.isTextBased()) return;
    const embed = new EmbedBuilder()
      .setTitle(`Goodbye ${member.displayName}`)
      .setDescription(`We hope to see you later ${member.displayName}.`)
      .setColor("Red");
    if (!channelRes.permissionsFor(this.selfMemberId)) return;
    if (!channelRes.permissionsFor(this.selfMemberId)!.has("SendMessages"))
      return;
    await channelRes.send({ embeds: [embed] });
  }
}
