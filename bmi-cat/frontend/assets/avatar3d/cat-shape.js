export function reshapeCat(geometry,original,settings){
 const p=geometry.attributes.position;
 const girth={emaciated:.78,slim:.88,medium:1,large:1.14,xxl:1.27}[settings.body]??1;
 for(let i=0;i<p.count;i++){
  const x=original[i*3],y=original[i*3+1],z=original[i*3+2];
  // Smooth deformation of the torso, tapering to zero at neck and paws.
  const vertical=Math.exp(-Math.pow((y-.8)/.42,4));
  const central=Math.exp(-Math.pow(x/.62,6)-Math.pow(z/.57,6));
  const factor=1+(girth-1)*vertical*central;
  p.setXYZ(i,x*factor,y,z*factor);
 }
 p.needsUpdate=true;geometry.computeVertexNormals();geometry.computeBoundingSphere();
}
