import {World} from '../领域/世界';
import type {Position} from '../领域/世界';
import type {Action} from './类型';
export class ActionRunner {
  private queue:Action[]=[];
  private current?:{action:Action;elapsed:number;from?:Position;curtain?:number};
  constructor(private world:World){}
  start(actions:Action[]) { this.clear();this.queue=[...actions]; }
  clear(){this.queue=[];this.current=undefined;}
  get busy(){return !!this.current||this.queue.length>0;}
  update(dt:number){
    if(!this.current){
      const action=this.queue.shift();if(!action)return;
      if(action.kind==='pose'){this.world.actor(action.actor).pose=action.pose;return;}
      if(action.kind==='turn'){this.world.actor(action.actor).heading=action.heading;return;}
      if(action.kind==='prop'){this.world.actor(action.actor).prop=action.prop;return;}
      if(action.kind==='move'){
        const actor=this.world.actor(action.actor);
        if(!this.world.room.canMove(actor.position,action.to,this.world.curtain)) {this.queue=[];throw new Error('幕布尚未打开，不能穿过幕布');}
        actor.pose='standing';
        actor.heading=Math.atan2(action.to[0]-actor.position[0],action.to[2]-actor.position[2]);
        this.current={action,elapsed:0,from:[...actor.position]};
      } else this.current={action,elapsed:0,curtain:this.world.curtain.progress};
    }
    const c=this.current;if(!c)return;c.elapsed+=dt;
    const action=c.action;
    if(action.kind!=='move'&&action.kind!=='curtain')return;
    const t=Math.min(1,c.elapsed/(action.seconds??1));const smooth=t*t*(3-2*t);
    if(action.kind==='move')this.world.actor(action.actor).position=c.from!.map((v,i)=>v+(action.to[i]-v)*smooth) as Position;
    else this.world.curtain.progress=c.curtain!+((action.open?1:0)-c.curtain!)*smooth;
    if(t===1)this.current=undefined;
  }
}
