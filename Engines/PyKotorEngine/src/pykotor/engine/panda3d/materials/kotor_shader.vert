#version 150

// Panda3D vertex shader for KotOR materials.
// References:
//   vendor/reone/shaders/model_vert.glsl - Vertex transform
//   /panda3d/panda3d-docs/programming/internal-structures/procedural-generation/creating-vertex-data.rst

uniform mat4 p3d_ModelViewProjectionMatrix;
uniform mat4 p3d_ModelViewMatrix;
uniform mat3 p3d_NormalMatrix;

in vec4 p3d_Vertex;
in vec3 p3d_Normal;
in vec2 p3d_MultiTexCoord0;
in vec2 p3d_MultiTexCoord1;
in vec3 p3d_Tangent;
in vec3 p3d_Binormal;

out vec3 v_view_pos;
out vec3 v_view_normal;
out vec2 v_uv0;
out vec2 v_uv1;
out mat3 v_tbn;

void main() {
    gl_Position = p3d_ModelViewProjectionMatrix * p3d_Vertex;
    vec4 view_pos = p3d_ModelViewMatrix * p3d_Vertex;
    v_view_pos = view_pos.xyz;

    vec3 normal = normalize(p3d_NormalMatrix * p3d_Normal);
    vec3 tangent = normalize(p3d_NormalMatrix * p3d_Tangent);
    vec3 binormal = normalize(p3d_NormalMatrix * p3d_Binormal);

    v_view_normal = normal;
    v_uv0 = p3d_MultiTexCoord0;
    v_uv1 = p3d_MultiTexCoord1;
    v_tbn = mat3(tangent, binormal, normal);
}

