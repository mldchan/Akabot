export type ViolationCountersMessageData = { messageIDs: string[] };
export type ViolationCountersData<T> = { serverId: string; eventId: string; violationsCount: number; expiryDate: Date; data?: T }[];

export class ViolationCounters {
    violationCounters = [] as ViolationCountersData<any>;
    vlNew(serverId: string, eventId: string, vlTime: number): number {
        this.violationCounters = this.violationCounters.filter((vl) => vl.expiryDate > new Date());
        const vl = this.violationCounters.find((vl) => vl.serverId === serverId && vl.eventId === eventId);
        if (vl) {
            vl.violationsCount++;
            vl.expiryDate = new Date(new Date().getTime() + vlTime);
            return vl.violationsCount;
        }
        this.violationCounters.push({
            serverId,
            eventId,
            violationsCount: 1,
            expiryDate: new Date(new Date().getTime() + vlTime)
        });
        return 1;
    }
    vlGetExtraData<T>(serverId: string, eventId: string): T | undefined {
        const vl = this.violationCounters.find((vl) => vl.serverId === serverId && vl.eventId === eventId);
        if (!vl) return undefined;
        return vl.data as T;
    }
    vlSetExtraData<T>(serverId: string, eventId: string, extraData: T): void {
        const vl = this.violationCounters.find((vl) => vl.serverId === serverId && vl.eventId === eventId);
        if (!vl) return;
        vl.data = extraData;
    }
    vlDelete(serverId: string, eventId: string): void {
        this.violationCounters = this.violationCounters.filter((vl) => vl.serverId !== serverId && vl.eventId !== eventId);
    }
}
