#version 150

// Panda3D fragment shader for KotOR materials.
// References:
//   vendor/reone/shaders/model_frag.glsl - Lighting model
//   /panda3d/panda3d-docs/programming/shaders/list-of-glsl-inputs.rst

uniform sampler2D p3d_Texture0;
uniform sampler2D p3d_Texture1;
uniform sampler2D p3d_Texture2;

uniform bool has_normal_map;
uniform bool has_lightmap;
uniform bool has_alpha;

in vec3 v_view_pos;
in vec3 v_view_normal;
in vec2 v_uv0;
in vec2 v_uv1;
in mat3 v_tbn;

out vec4 p3d_FragColor;

void main() {
    vec4 base_color = texture(p3d_Texture0, v_uv0);
    if (has_alpha && base_color.a < 0.01) {
        discard;
    }

    vec3 normal = v_view_normal;
    if (has_normal_map) {
        vec3 n = texture(p3d_Texture1, v_uv0).xyz * 2.0 - 1.0;
        normal = normalize(v_tbn * n);
    } else {
        normal = normalize(normal);
    }

    vec3 view_dir = normalize(-v_view_pos);
    vec3 light_dir = normalize(vec3(0.3, 0.7, 0.6));
    vec3 light_color = vec3(1.0);

    float diff = max(dot(normal, light_dir), 0.0);
    vec3 diffuse = diff * light_color;

    vec3 half_dir = normalize(light_dir + view_dir);
    float spec = pow(max(dot(normal, half_dir), 0.0), 32.0);
    vec3 specular = spec * light_color * 0.15;

    vec3 color = base_color.rgb * (0.2 + diffuse) + specular;

    if (has_lightmap) {
        vec3 lightmap = texture(p3d_Texture2, v_uv1).rgb;
        color *= lightmap;
    }

    p3d_FragColor = vec4(color, base_color.a);
}

