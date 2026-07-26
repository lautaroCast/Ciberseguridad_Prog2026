import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { createTarget, listTargets, updateTarget } from "../api";
import { ErrorBanner } from "../components/ErrorBanner";
import { Spinner } from "../components/Spinner";

export function TargetsPage() {
  const queryClient = useQueryClient();
  const targetsQuery = useQuery({ queryKey: ["targets"], queryFn: () => listTargets() });

  const [name, setName] = useState("");
  const [host, setHost] = useState("");
  const [description, setDescription] = useState("");

  const createMutation = useMutation({
    mutationFn: () => createTarget({ name, host, description: description || null }),
    onSuccess: () => {
      setName("");
      setHost("");
      setDescription("");
      queryClient.invalidateQueries({ queryKey: ["targets"] });
    },
  });

  const toggleActiveMutation = useMutation({
    mutationFn: ({ id, isActive }: { id: string; isActive: boolean }) =>
      updateTarget(id, { is_active: isActive }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["targets"] }),
  });

  return (
    <div>
      <h1>Targets</h1>

      <form
        className="target-form"
        onSubmit={(event) => {
          event.preventDefault();
          createMutation.mutate();
        }}
      >
        <input
          placeholder="Nombre"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
        />
        <input
          placeholder="Host (juice-shop, dvwa)"
          value={host}
          onChange={(event) => setHost(event.target.value)}
          required
        />
        <input
          placeholder="Descripción (opcional)"
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <button type="submit" disabled={createMutation.isPending}>
          Crear target
        </button>
      </form>
      <ErrorBanner error={createMutation.error} />

      {targetsQuery.isLoading && <Spinner />}
      <ErrorBanner error={targetsQuery.error} />

      {targetsQuery.data && (
        <table className="target-table">
          <thead>
            <tr>
              <th>Nombre</th>
              <th>Host</th>
              <th>Activo</th>
              <th>Creado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {targetsQuery.data.map((target) => (
              <tr key={target.id}>
                <td>{target.name}</td>
                <td>{target.host}</td>
                <td>
                  <button
                    type="button"
                    className={`badge badge--${target.is_active ? "active" : "inactive"}`}
                    onClick={() =>
                      toggleActiveMutation.mutate({ id: target.id, isActive: !target.is_active })
                    }
                  >
                    {target.is_active ? "Activo" : "Inactivo"}
                  </button>
                </td>
                <td>{new Date(target.created_at).toLocaleString()}</td>
                <td>
                  <Link to={`/targets/${target.id}`}>Ver detalle</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
