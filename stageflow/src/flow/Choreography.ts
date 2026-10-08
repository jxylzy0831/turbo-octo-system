import type {Action,Beat,ScriptData} from './types';
import type {ActorId} from '../domain/World';
export class Choreography {
  compile(script:ScriptData):Beat[] {
    const beats:Beat[]=[];
    script.scenes.forEach((scene,si)=>{
      scene.entries.forEach((entry,ei)=>{
        const speaker=/^(G|N[1-4]|P[1-4])$/.test(entry.label) ? entry.label as ActorId : undefined;
        const actions:Action[]=[];
        if(ei===0 && si>=1 && si<=4) {
          const n=('N'+si) as ActorId;
          // 新场地幕布横贯全宽，演员首个出场需先打开，再通过中部进入玩家区。
          actions.push({kind:'curtain',open:true,seconds:1.8});
          actions.push({kind:'move',actor:n,to:[0,0,-5.5],seconds:1});
          actions.push({kind:'move',actor:n,to:[0,0,-1.1],seconds:1.5});
          actions.push({kind:'prop',actor:n,prop:['','欢迎袋','失物招领','杯具箱','布'][si]});
        }
        if(ei===scene.entries.length-1 && si>=1 && si<=4) {
          const n=('N'+si) as ActorId;
          actions.push({kind:'move',actor:n,to:[0,0,1.1],seconds:1.2});
          actions.push({kind:'move',actor:n,to:[4.65,0,1.1],seconds:1.3});
          actions.push({kind:'move',actor:n,to:[4.65,0,4.5],seconds:1.2});
          actions.push({kind:'move',actor:n,to:[-3.3+(si-1)*2.2+.65,0,4.5],seconds:1.5});
          actions.push({kind:'move',actor:n,to:[-3.3+(si-1)*2.2+.65,0,3.5],seconds:.6},{kind:'turn',actor:n,heading:Math.PI},{kind:'pose',actor:n,pose:'seated'});
        }
        if(si===5 && ei===0) actions.push({kind:'move',actor:'G',to:[0,0,-2.4],seconds:1.3});
        if(si===5 && ei===1) actions.push({kind:'move',actor:'G',to:[-4.25,0,2.5],seconds:1.5},{kind:'pose',actor:'G',pose:'seated'});
        if(si===6 && ei===0) actions.push({kind:'pose',actor:'G',pose:'standing'},{kind:'move',actor:'G',to:[0,0,1.8],seconds:1});
        if(si===7 && ei===0) actions.push({kind:'prop',actor:'G',prop:'课表'});
        if(si===9 && ei===0) actions.push({kind:'prop',actor:'G',prop:'手机'});
        if(si===9 && entry.text.includes('给自己添一把椅子')) actions.push({kind:'move',actor:'G',to:[-4.25,0,2.5],seconds:1.3},{kind:'pose',actor:'G',pose:'seated'});
        const wait=entry.label==='玩家入口';
        const pair=si>=1&&si<=4 ? si : (entry.text.match(/P([1-4])/)?.[1]??1);
        beats.push({scene:si,entry,speaker,actions,wait,waitActor:('P'+pair) as ActorId});
      });
    });
    return beats;
  }
}
