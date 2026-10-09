import * as THREE from 'three';
import {ActorModel,colors} from '../领域/世界';
export class ActorView {
  readonly group=new THREE.Group();
  private upper=new THREE.Group();
  private legs=new THREE.Group();
  private material:THREE.MeshStandardMaterial;
  private ring:THREE.Mesh;
  private prop=new THREE.Group();
  private lastProp='';
  constructor(readonly model:ActorModel){
    this.material=new THREE.MeshStandardMaterial({color:colors[model.id],roughness:.5});
    const head=new THREE.Mesh(new THREE.SphereGeometry(.15,18,14),this.material);head.position.y=1.58;this.upper.add(head);
    this.line([0,1.4,0],[0,.85,0],this.upper,.045);
    this.line([0,1.32,0],[-.23,1.08,0],this.upper);
    this.line([-.23,1.08,0],[-.34,.93,.06],this.upper);
    this.line([0,1.32,0],[.23,1.08,0],this.upper);
    this.line([.23,1.08,0],[.34,.93,.06],this.upper);
    this.line([0,.85,0],[-.15,.43,0],this.legs);
    this.line([-.15,.43,0],[-.19,.09,.06],this.legs);
    this.line([0,.85,0],[.15,.43,0],this.legs);
    this.line([.15,.43,0],[.19,.09,.06],this.legs);
    this.group.add(this.upper,this.legs,this.prop);
    for(const x of [-.055,.055]){const eye=new THREE.Mesh(new THREE.SphereGeometry(.024,8,8),new THREE.MeshBasicMaterial({color:0x142326}));eye.position.set(x,1.6,.137);this.upper.add(eye);}
    this.ring=new THREE.Mesh(new THREE.RingGeometry(.29,.34,40),new THREE.MeshBasicMaterial({color:colors[model.id],transparent:true,opacity:.25,side:THREE.DoubleSide}));
    this.ring.rotation.x=-Math.PI/2;this.ring.position.y=.012;this.group.add(this.ring);
  }
  private line(a:number[],b:number[],parent:THREE.Group,r=.032){
    const start=new THREE.Vector3(...a as [number,number,number]),end=new THREE.Vector3(...b as [number,number,number]);
    const mesh=new THREE.Mesh(new THREE.CylinderGeometry(r,r,start.distanceTo(end),8),this.material);
    mesh.position.copy(start.clone().add(end).multiplyScalar(.5));mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),end.sub(start).normalize());parent.add(mesh);
  }
  update(active:boolean,time:number){
    this.group.position.set(...this.model.position);this.group.rotation.y=this.model.heading;this.group.visible=this.model.visible;
    const sit=this.model.pose==='seated';this.upper.position.y=sit?-.38:0;this.legs.scale.y=sit?.55:1;
    this.upper.rotation.z=active?Math.sin(time*3)*.025:0;
    this.ring.scale.setScalar(active?1.4:1);(this.ring.material as THREE.MeshBasicMaterial).opacity=active?.9:.22;
    this.material.emissive.set(active?colors[this.model.id]:'#000000');this.material.emissiveIntensity=active?.2:0;
    if(this.lastProp!==this.model.prop){
      this.lastProp=this.model.prop;this.prop.clear();
      if(this.lastProp){const box=new THREE.Mesh(new THREE.BoxGeometry(.38,.3,.22),new THREE.MeshStandardMaterial({color:0xd8d2bc}));box.position.set(.37,1,.18);this.prop.add(box);}
    }
    this.prop.position.y=sit?-.38:0;
  }
}
