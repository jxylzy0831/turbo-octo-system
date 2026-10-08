export type ActorId = 'G' | 'N1' | 'N2' | 'N3' | 'N4' | 'P1' | 'P2' | 'P3' | 'P4';
export type Position = [number, number, number];
export type Pose = 'standing' | 'seated' | 'wave';
export const ids: ActorId[] = ['G', 'P1', 'N1', 'P2', 'N2', 'P3', 'N3', 'P4', 'N4'];
export const colors: Record<ActorId, string> = { G:'#61d6ba', P1:'#f2b769',N1:'#f2b769',P2:'#79a8f8',N2:'#79a8f8',P3:'#b695ec',N3:'#b695ec',P4:'#ec94b9',N4:'#ec94b9' };
export class ActorModel {
  position: Position;
  heading = Math.PI;
  pose: Pose = 'standing';
  visible = true;
  prop = '';
  constructor(readonly id: ActorId, position: Position) { this.position = [...position]; }
}
export class CurtainModel {
  progress = 0;
  get state() { return this.progress <= 0 ? 'closed' : this.progress >= 1 ? 'open' : 'moving'; }
}
export class RoomModel {
  readonly width = 10;
  readonly depth = 12;
  readonly curtainZ = 0;
  readonly northDoor: Position = [0,0,-6];
  readonly southDoor: Position = [0,0,6];
  canMove(from: Position, to: Position, curtain: CurtainModel) {
    return !(from[2] * to[2] < 0 && curtain.progress < .98);
  }
}
export interface Snapshot { actors: {id:ActorId; position:Position; heading:number; pose:Pose; visible:boolean;prop:string}[]; curtain:number }
export class World {
  room = new RoomModel();
  curtain = new CurtainModel();
  actors = new Map<ActorId, ActorModel>();
  constructor() { this.reset(); }
  reset() {
    this.curtain.progress = 0;
    const put = (actor: ActorModel) => {
      const existing = this.actors.get(actor.id);
      if (existing) Object.assign(existing, actor);
      else this.actors.set(actor.id, actor);
    };
    put(new ActorModel('G',[-3.8,0,1.25]));
    for (let i=1;i<=4;i++) {
      const p = new ActorModel(('P'+i) as ActorId, [-3.3+(i-1)*2.2,0,3.6]);
      p.pose='seated'; p.heading=Math.PI; put(p);
      const n=new ActorModel(('N'+i) as ActorId, [-3+(i-1)*2,0,-4.4]);
      n.heading=0; put(n);
    }
  }
  actor(id:ActorId) { return this.actors.get(id)!; }
  snapshot():Snapshot { return {curtain:this.curtain.progress,actors:[...this.actors.values()].map(a=>({...a,position:[...a.position]}))}; }
  restore(s:Snapshot) { this.curtain.progress=s.curtain; for(const item of s.actors) Object.assign(this.actor(item.id),item,{position:[...item.position]}); }
}
