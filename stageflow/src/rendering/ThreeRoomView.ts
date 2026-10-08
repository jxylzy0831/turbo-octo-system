import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {World} from '../domain/World';
import type {ActorId} from '../domain/World';
import {ActorView} from './ActorView';
export type ViewMode='director'|'top'|'player';
export class ThreeRoomView {
  readonly scene=new THREE.Scene();
  readonly camera=new THREE.OrthographicCamera(-10,10,10,-10,.1,100);
  readonly renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});
  readonly controls:OrbitControls;
  readonly actors=new Map<ActorId,ActorView>();
  private curtains:THREE.Mesh[]=[];
  mode:ViewMode='director';
  constructor(private world:World,readonly container:HTMLElement){
    this.renderer.setPixelRatio(Math.min(devicePixelRatio,2));this.renderer.setClearColor(0x142326,1);
    container.append(this.renderer.domElement);this.scene.add(new THREE.HemisphereLight(0xddefff,0x697463,2));
    const sun=new THREE.DirectionalLight(0xffffff,2.2);sun.position.set(4,12,8);this.scene.add(sun);
    this.controls=new OrbitControls(this.camera,this.renderer.domElement);this.controls.enableDamping=true;this.controls.maxPolarAngle=Math.PI/2.05;this.controls.minZoom=.65;this.controls.maxZoom=2.5;
    this.build();for(const a of world.actors.values()){const view=new ActorView(a);this.actors.set(a.id,view);this.scene.add(view.group);}
    this.setCamera('director');new ResizeObserver(()=>this.resize()).observe(container);this.resize();
  }
  private box(w:number,h:number,d:number,x:number,y:number,z:number,color:number){
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(w,h,d),new THREE.MeshStandardMaterial({color,roughness:.8}));mesh.position.set(x,y,z);this.scene.add(mesh);return mesh;
  }
  private label(text:string,x:number,z:number){
    const canvas=document.createElement('canvas');canvas.width=768;canvas.height=128;
    const ctx=canvas.getContext('2d')!;ctx.font='bold 58px Microsoft YaHei';ctx.textAlign='center';ctx.fillStyle='#c7d7ca';ctx.fillText(text,384,86);
    const plane=new THREE.Mesh(new THREE.PlaneGeometry(3.7,.62),new THREE.MeshBasicMaterial({map:new THREE.CanvasTexture(canvas),transparent:true,depthWrite:false}));plane.rotation.x=-Math.PI/2;plane.position.set(x,.025,z);this.scene.add(plane);
  }
  private build(){
    this.box(10,.12,6,0,-.08,-3,0x38484a);this.box(10,.12,6,0,-.08,3,0x485348);
    for(const z of [-6,6])for(const x of [-2.85,2.85])this.box(4.3,.65,.14,x,.3,z,0x7b8b82);
    for(const x of [-5,5])this.box(.14,.65,12,x,.3,0,0x7b8b82);
    for(const z of [-6,6]){this.box(.1,2.65,.16,-.7,1.3,z,0xe7cc8c);this.box(.1,2.65,.16,.7,1.3,z,0xe7cc8c);this.box(1.5,.1,.16,0,2.65,z,0xe7cc8c);}
    this.label('北门 · NPC 入口',0,-5.35);this.label('南门 · 玩家入口',0,5.35);this.label('演绎 / 备场区',0,-3.4);this.label('玩家区',0,4.7);
    this.box(10,.07,.14,0,2.9,0,0xb8a585);
    for(const sign of [-1,1]){const panel=this.box(1,2.75,.1,0,1.37,0,0x965348);panel.userData.sign=sign;this.curtains.push(panel);}
    this.box(8.4,.12,1.15,0,.85,2.6,0x9b8566);
    for(const x of [-3.7,3.7])for(const z of [2.2,3])this.box(.1,.85,.1,x,.42,z,0x706650);
    for(let i=0;i<4;i++)for(const x of [-3.3+i*2.2,-2.65+i*2.2]){this.box(.46,.1,.44,x,.45,3.65,0x8c9a84);this.box(.46,.58,.06,x,.76,3.9,0x8c9a84);}
    this.box(.5,.1,.45,-4.25,.45,2.5,0x8c9a84);this.box(2,.12,1,0,.85,-2.5,0x9b8566);
  }
  setCamera(mode:ViewMode){
    this.mode=mode;this.controls.enabled=mode!=='player';this.controls.target.set(0,.45,0);
    if(mode==='director')this.camera.position.set(11,13,16);
    if(mode==='top')this.camera.position.set(.01,22,.01);
    if(mode==='player'){this.camera.position.set(0,4.4,11);this.controls.target.set(0,1,-1.5);}
    this.camera.zoom=1;this.camera.lookAt(this.controls.target);this.camera.updateProjectionMatrix();this.controls.update();
  }
  resize(){const w=this.container.clientWidth,h=this.container.clientHeight,aspect=w/Math.max(1,h);const size=9;this.camera.left=-size*aspect;this.camera.right=size*aspect;this.camera.top=size;this.camera.bottom=-size;this.camera.updateProjectionMatrix();this.renderer.setSize(w,h);}
  isVisible(id:ActorId){return this.world.actor(id).visible && !(this.mode==='player'&&this.world.actor(id).position[2]<0&&this.world.curtain.progress<.98);}
  update(active:ActorId|undefined,time:number){
    const width=Math.max(.08,5*(1-this.world.curtain.progress));for(const p of this.curtains){p.scale.x=width;p.position.x=p.userData.sign*(5-width/2);}
    for(const [id,v] of this.actors){v.update(id===active,time);v.group.visible=this.isVisible(id);}
    this.controls.update();this.renderer.render(this.scene,this.camera);
  }
  project(id:ActorId){
    const actor=this.world.actor(id),v=new THREE.Vector3(...actor.position);v.y+=actor.pose==='seated'?1.5:1.95;v.project(this.camera);
    return {x:(v.x*.5+.5)*this.container.clientWidth,y:(-.5*v.y+.5)*this.container.clientHeight,onScreen:v.z>=-1&&v.z<=1&&Math.abs(v.x)<1.05&&Math.abs(v.y)<1.1};
  }
}
