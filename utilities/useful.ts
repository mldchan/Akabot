import {
    AuditLogEvent,
    Guild,
    GuildMember,
    NewsChannel,
    PrivateThreadChannel,
    PublicThreadChannel,
    StageChannel,
    TextChannel,
    VoiceChannel
} from "discord.js";
import { getSetting } from "../data/settings";

export function getLogChannel(
    guild: Guild
):
    | NewsChannel
    | StageChannel
    | TextChannel
    | PrivateThreadChannel
    | PublicThreadChannel<boolean>
    | VoiceChannel
    | undefined {
    const channelID = getSetting(guild.id, "loggingChannel");
    const channel = guild.channels.cache.get(channelID);
    if (!channel?.isTextBased()) return undefined;
    return channel;
}

export function getSelfMember(guild: Guild): GuildMember | undefined {
    return guild.members.cache.get(guild.client.user?.id ?? "");
}
export async function fetchAuditLog(guild: Guild, event: AuditLogEvent): Promise<string> {
    const selfMember = getSelfMember(guild);
    if (!selfMember) return "Error: No self member";

    if (!selfMember.permissions.has("ViewAuditLog")) {
        return "Error: No `View Audit Log` permission";
    }

    let entry = (await guild.fetchAuditLogs({ limit: 1, type: event })).entries.first();
    if (!entry) return "Error: No entry found";
    return entry.executor?.username ?? "Unknown";
}
