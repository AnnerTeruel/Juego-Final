import os
import math

os.makedirs('assets', exist_ok=True)

with open('assets/spiked_barrel.obj', 'w') as f:
    f.write("o SpikedBarrel\n")
    segments = 12
    radius = 0.5
    height = 1.0
    
    vertices = []
    normals = []
    uvs = []
    faces = []
    
    # --- CUERPO DEL BARRIL ---
    for i in range(segments):
        angle = 2.0 * math.pi * i / segments
        x = radius * math.cos(angle)
        z = radius * math.sin(angle)
        vertices.append((x, height/2, z))
        vertices.append((x, -height/2, z))
        normals.append((math.cos(angle), 0, math.sin(angle)))
        normals.append((math.cos(angle), 0, math.sin(angle)))
        uvs.append((i/segments, 1.0))
        uvs.append((i/segments, 0.0))
        
    for i in range(segments):
        next_i = (i + 1) % segments
        tl = i * 2 + 1; bl = i * 2 + 2
        tr = next_i * 2 + 1; br = next_i * 2 + 2
        faces.append([tl, bl, br, tr])
        
    # --- PÚAS (SPIKES) ---
    spike_heights = [-0.25, 0.25]
    spike_base = 0.1
    spike_length = 0.3
    
    # Generar púas en 8 direcciones
    for h in spike_heights:
        for i in range(8):
            angle = 2.0 * math.pi * i / 8
            cx = radius * math.cos(angle)
            cz = radius * math.sin(angle)
            
            # Vectores direccionales
            forward = (math.cos(angle), 0, math.sin(angle))
            right = (-math.sin(angle), 0, math.cos(angle))
            
            # Vértices de la púa (4 base, 1 punta)
            v_start = len(vertices) + 1
            
            # Punta
            tip_x = cx + forward[0] * spike_length
            tip_z = cz + forward[2] * spike_length
            vertices.append((tip_x, h, tip_z))
            normals.append(forward)
            uvs.append((0.5, 0.5)) # UV genérico
            
            # Base 4 esquinas
            for bx, by in [(-1,-1), (1,-1), (1,1), (-1,1)]:
                px = cx + right[0] * bx * spike_base
                pz = cz + right[2] * bx * spike_base
                py = h + by * spike_base
                vertices.append((px, py, pz))
                normals.append(forward)
                uvs.append((0.5, 0.5))
                
            # Caras de la pirámide (4 triángulos)
            # Punta es v_start, base son v_start+1 a v_start+4
            faces.append([v_start, v_start+1, v_start+2])
            faces.append([v_start, v_start+2, v_start+3])
            faces.append([v_start, v_start+3, v_start+4])
            faces.append([v_start, v_start+4, v_start+1])

    # --- ESCRIBIR ARCHIVO ---
    for v in vertices:
        f.write(f"v {v[0]:.4f} {v[1]:.4f} {v[2]:.4f}\n")
    for vn in normals:
        f.write(f"vn {vn[0]:.4f} {vn[1]:.4f} {vn[2]:.4f}\n")
    for vt in uvs:
        f.write(f"vt {vt[0]:.4f} {vt[1]:.4f}\n")
        
    for face in faces:
        if len(face) == 4:
            f.write(f"f {face[0]}/{face[0]}/{face[0]} {face[1]}/{face[1]}/{face[1]} {face[2]}/{face[2]}/{face[2]}\n")
            f.write(f"f {face[0]}/{face[0]}/{face[0]} {face[2]}/{face[2]}/{face[2]} {face[3]}/{face[3]}/{face[3]}\n")
        else:
            f.write(f"f {face[0]}/{face[0]}/{face[0]} {face[1]}/{face[1]}/{face[1]} {face[2]}/{face[2]}/{face[2]}\n")

print("Modelo de barril con púas generado en assets/spiked_barrel.obj")
